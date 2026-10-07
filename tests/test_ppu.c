#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stddef.h>
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

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);
extern void gbb_test_ppu_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_ppu_observer_count(const gbb_instance *);

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

static gbb_instance *load_guest_with_tail(const guest_program *p, uint8_t lcdc,
                                          const uint8_t *tail, size_t tail_size) {
    if (p->size > sizeof(p->bytes) - 4u || tail_size > sizeof(p->bytes) - p->size - 4u)
        return NULL;
    uint8_t rom[32768] = {0};
    /* Keep the guest body beyond the cartridge header and checksum bytes. */
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    guest_program complete = *p;
    emit_reg(&complete, 0x40, lcdc);
    for (size_t i = 0; i < tail_size; ++i) emit(&complete, tail[i]);
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

static gbb_instance *load_guest(const guest_program *p, uint8_t lcdc) {
    return load_guest_with_tail(p, lcdc, NULL, 0);
}

static void emit_read_to_wram(guest_program *p, uint8_t register_address,
                              uint16_t ram_address) {
    emit(p, 0xF0); emit(p, register_address); /* LDH A,[n] */
    emit(p, 0xEA); emit(p, (uint8_t)ram_address); /* LD [nn],A */
    emit(p, (uint8_t)(ram_address >> 8));
}

static const gbb_test_bus_event *find_bus_event(const gbb_test_bus_event *events,
                                                 size_t count, uint16_t address,
                                                 uint8_t access, int value) {
    for (size_t i = 0; i < count; ++i)
        if (events[i].address == address && events[i].access == access &&
            (value < 0 || events[i].value == (uint8_t)value)) return &events[i];
    return NULL;
}

static const gbb_test_bus_event *find_ppu_event(const gbb_test_bus_event *events,
                                                 size_t count, uint8_t access,
                                                 int value,
                                                 uint64_t at_or_after) {
    for (size_t i = 0; i < count; ++i)
        if (events[i].access == access &&
            (value < 0 || events[i].value == (uint8_t)value) &&
            events[i].time_half_dots >= at_or_after) return &events[i];
    return NULL;
}

static int stat_sample(uint8_t scx, uint8_t lcdc, unsigned nop_count,
                       uint8_t stat, uint8_t lyc, uint64_t expected_delta,
                       uint8_t expected_mode) {
    guest_program p = {0};
    start_guest(&p);
    emit_reg(&p, 0x41, stat);
    emit_reg(&p, 0x45, lyc);
    emit_reg(&p, 0x43, scx);
    uint8_t tail[256];
    if (nop_count + 5u > sizeof(tail)) return 1;
    memset(tail, 0, nop_count);
    tail[nop_count] = 0xF0; tail[nop_count + 1u] = 0x41;
    tail[nop_count + 2u] = 0xEA; tail[nop_count + 3u] = 0x00;
    tail[nop_count + 4u] = 0xC0;
    gbb_instance *machine = load_guest_with_tail(&p, lcdc, tail, nop_count + 5u);
    REQUIRE(machine != NULL);
    gbb_test_bus_event events[512];
    gbb_test_observer_set(machine, events, 512);
    gbb_run_result run = gbb_run(machine, (uint64_t)nop_count * 8u + 1024u, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    size_t count = gbb_test_observer_count(machine);
    const gbb_test_bus_event *enable = find_bus_event(events, count, 0xFF40, 2, lcdc);
    const gbb_test_bus_event *read = find_bus_event(events, count, 0xFF41, 1, -1);
    REQUIRE(enable != NULL && read != NULL);
    REQUIRE(read->time_half_dots - enable->time_half_dots == expected_delta);
    REQUIRE((read->value & 3u) == expected_mode);
    REQUIRE(gbb_peek_ram(machine, 0xC000) == read->value);
    gbb_destroy(machine);
    return 0;
}

static int fetch_mode0_dot(uint8_t scx, uint8_t lcdc, uint8_t wy, uint8_t wx,
                           const uint8_t *oam, size_t oam_size,
                           uint16_t expected_dot) {
    guest_program p = {0};
    start_guest(&p);
    emit_reg(&p, 0x43, scx);
    emit_reg(&p, 0x4A, wy);
    emit_reg(&p, 0x4B, wx);
    if (oam != NULL) emit_bytes(&p, 0xFE00, oam, oam_size);
    gbb_instance *machine = load_guest(&p, lcdc);
    REQUIRE(machine != NULL);
    gbb_test_bus_event bus_events[256];
    gbb_test_bus_event ppu_events[64];
    gbb_test_observer_set(machine, bus_events, 256);
    gbb_test_ppu_observer_set(machine, ppu_events, 64);
    gbb_run_result run = gbb_run(machine, 1800, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    size_t bus_count = gbb_test_observer_count(machine);
    size_t ppu_count = gbb_test_ppu_observer_count(machine);
    const gbb_test_bus_event *enable = find_bus_event(bus_events, bus_count, 0xFF40, 2, lcdc);
    REQUIRE(enable != NULL);
    const gbb_test_bus_event *mode0 = find_ppu_event(ppu_events, ppu_count, 4, 0,
                                                      enable->time_half_dots);
    if (mode0 == NULL) {
        fprintf(stderr, "missing mode0 scx=%u lcdc=%02x wx=%u objects=%zu count=%zu enable=%llu\n",
                scx, lcdc, wx, oam_size / 4u, ppu_count,
                (unsigned long long)enable->time_half_dots);
        for (size_t i = 0; i < ppu_count; ++i)
            fprintf(stderr, "ppu[%zu] t=%llu access=%u value=%u\n", i,
                    (unsigned long long)ppu_events[i].time_half_dots,
                    ppu_events[i].access, ppu_events[i].value);
    }
    REQUIRE(mode0 != NULL);
    REQUIRE(mode0->time_half_dots - enable->time_half_dots == (uint64_t)expected_dot * 2u);
    gbb_destroy(machine);
    return 0;
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

static int ppu_timing_fetch(void) {
    REQUIRE(stat_sample(3, 0x91, 60, 0, 0, 504, 3) == 0);
    REQUIRE(fetch_mode0_dot(0, 0xF1, 0, 7, NULL, 0, 258) == 0);
    REQUIRE(fetch_mode0_dot(3, 0xF1, 0, 0, NULL, 0, 260) == 0);

    const uint8_t object_x8[] = {16, 8, 0, 0};
    const uint8_t object_x14[] = {16, 14, 0, 0};
    const uint8_t objects_same_tile[] = {16, 8, 0, 0, 16, 12, 0, 0};
    REQUIRE(fetch_mode0_dot(0, 0x93, 0, 0, object_x8, sizeof(object_x8), 263) == 0);
    REQUIRE(fetch_mode0_dot(0, 0x93, 0, 0, object_x14, sizeof(object_x14), 258) == 0);
    REQUIRE(fetch_mode0_dot(0, 0x93, 0, 0, objects_same_tile,
                            sizeof(objects_same_tile), 269) == 0);
    return 0;
}

static int ppu_timing_modes(void) {
    guest_program p = {0};
    start_guest(&p);
    gbb_instance *machine = load_guest(&p, 0x91);
    REQUIRE(machine != NULL);
    gbb_test_bus_event bus_events[256], ppu_events[64];
    gbb_test_observer_set(machine, bus_events, 256);
    gbb_test_ppu_observer_set(machine, ppu_events, 64);
    gbb_run_result run = gbb_run(machine, 1100, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    size_t bus_count = gbb_test_observer_count(machine);
    size_t ppu_count = gbb_test_ppu_observer_count(machine);
    const gbb_test_bus_event *enable = find_bus_event(bus_events, bus_count, 0xFF40, 2, 0x91);
    REQUIRE(enable != NULL);
    const gbb_test_bus_event *mode3 = find_ppu_event(ppu_events, ppu_count, 4, 3,
                                                      enable->time_half_dots);
    const gbb_test_bus_event *mode0 = find_ppu_event(ppu_events, ppu_count, 4, 0,
                                                      enable->time_half_dots);
    const gbb_test_bus_event *next_mode2 = find_ppu_event(ppu_events, ppu_count, 4, 2,
                                                           enable->time_half_dots + 1u);
    REQUIRE(mode3 != NULL && mode0 != NULL && next_mode2 != NULL);
    REQUIRE(mode3->time_half_dots - enable->time_half_dots == 160u);
    REQUIRE(mode0->time_half_dots - enable->time_half_dots == 504u);
    REQUIRE(next_mode2->time_half_dots - enable->time_half_dots == 912u);
    gbb_destroy(machine);

    REQUIRE(stat_sample(0, 0x91, 59, 0, 0, 496, 3) == 0);
    REQUIRE(stat_sample(0, 0x91, 60, 0, 0, 504, 0) == 0);
    REQUIRE(stat_sample(0, 0x91, 61, 0, 0, 512, 0) == 0);
    REQUIRE(stat_sample(0, 0x91, 111, 0, 0, 912, 2) == 0);
    return 0;
}

static int ppu_timing_stat(void) {
    guest_program p = {0};
    start_guest(&p);
    emit_reg(&p, 0x41, 0x28);          /* Mode 0 and Mode 2 share one STAT line. */
    gbb_instance *machine = load_guest(&p, 0x91);
    REQUIRE(machine != NULL);
    gbb_test_bus_event bus_events[256], ppu_events[64];
    gbb_test_observer_set(machine, bus_events, 256);
    gbb_test_ppu_observer_set(machine, ppu_events, 64);
    gbb_run_result run = gbb_run(machine, 1600, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    size_t bus_count = gbb_test_observer_count(machine);
    size_t ppu_count = gbb_test_ppu_observer_count(machine);
    const gbb_test_bus_event *enable = find_bus_event(bus_events, bus_count, 0xFF40, 2, 0x91);
    REQUIRE(enable != NULL);
    uint64_t irq_times[4] = {0};
    size_t irq_count = 0;
    for (size_t i = 0; i < ppu_count; ++i) {
        if (ppu_events[i].access == 5 && irq_count < 4)
            irq_times[irq_count++] = ppu_events[i].time_half_dots;
    }
    REQUIRE(irq_count == 3);
    REQUIRE(irq_times[0] == enable->time_half_dots);
    REQUIRE(irq_times[1] - enable->time_half_dots == 504u);
    REQUIRE(irq_times[2] - enable->time_half_dots == 1416u);
    gbb_destroy(machine);

    memset(&p, 0, sizeof(p));
    start_guest(&p);
    emit_reg(&p, 0x41, 0x40);          /* LYC=1 is the sole enabled source. */
    emit_reg(&p, 0x45, 1);
    machine = load_guest(&p, 0x91);
    REQUIRE(machine != NULL);
    gbb_test_bus_event line_bus[256], line_ppu[64];
    gbb_test_observer_set(machine, line_bus, 256);
    gbb_test_ppu_observer_set(machine, line_ppu, 64);
    run = gbb_run(machine, 1100, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    bus_count = gbb_test_observer_count(machine);
    ppu_count = gbb_test_ppu_observer_count(machine);
    enable = find_bus_event(line_bus, bus_count, 0xFF40, 2, 0x91);
    REQUIRE(enable != NULL);
    irq_count = 0;
    for (size_t i = 0; i < ppu_count; ++i)
        if (line_ppu[i].access == 5) {
            REQUIRE(line_ppu[i].time_half_dots - enable->time_half_dots == 912u);
            ++irq_count;
        }
    REQUIRE(irq_count == 1);
    gbb_destroy(machine);
    return 0;
}

static int ppu_timing_lcd(void) {
    guest_program p = {0}, tail = {0};
    start_guest(&p);
    emit_reg(&p, 0x41, 0xFF);          /* only STAT interrupt-enable bits are writable */
    emit_reg(&p, 0x42, 0x12);
    emit_reg(&p, 0x43, 0x34);
    emit_reg(&p, 0x44, 0x55);          /* LY writes are ignored. */
    emit_reg(&p, 0x45, 0);
    emit_reg(&p, 0x47, 0xAB);
    emit_reg(&p, 0x48, 0xCD);
    emit_reg(&p, 0x49, 0xEF);
    emit_reg(&p, 0x4A, 1);
    emit_reg(&p, 0x4B, 7);
    emit_read_to_wram(&tail, 0x41, 0xC000);
    emit_read_to_wram(&tail, 0x40, 0xC001);
    emit_read_to_wram(&tail, 0x42, 0xC002);
    emit_read_to_wram(&tail, 0x43, 0xC003);
    emit_read_to_wram(&tail, 0x44, 0xC004);
    emit_read_to_wram(&tail, 0x45, 0xC005);
    emit_read_to_wram(&tail, 0x47, 0xC006);
    emit_read_to_wram(&tail, 0x48, 0xC007);
    emit_read_to_wram(&tail, 0x49, 0xC008);
    emit_read_to_wram(&tail, 0x4A, 0xC009);
    emit_read_to_wram(&tail, 0x4B, 0xC00A);
    emit_reg(&tail, 0x40, 0);
    emit_read_to_wram(&tail, 0x44, 0xC00B);
    emit_read_to_wram(&tail, 0x41, 0xC00C);
    emit_read_to_wram(&tail, 0x40, 0xC00D);
    emit_reg(&tail, 0x40, 0x91);
    emit_read_to_wram(&tail, 0x44, 0xC00E);
    emit_read_to_wram(&tail, 0x41, 0xC00F);
    gbb_instance *machine = load_guest_with_tail(&p, 0x91, tail.bytes, tail.size);
    REQUIRE(machine != NULL);
    gbb_run_result run = gbb_run(machine, 5000, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(machine, 0xC000) == 0xFE);
    REQUIRE(gbb_peek_ram(machine, 0xC001) == 0x91);
    REQUIRE(gbb_peek_ram(machine, 0xC002) == 0x12);
    REQUIRE(gbb_peek_ram(machine, 0xC003) == 0x34);
    REQUIRE(gbb_peek_ram(machine, 0xC004) == 0);
    REQUIRE(gbb_peek_ram(machine, 0xC005) == 0);
    REQUIRE(gbb_peek_ram(machine, 0xC006) == 0xAB);
    REQUIRE(gbb_peek_ram(machine, 0xC007) == 0xCD);
    REQUIRE(gbb_peek_ram(machine, 0xC008) == 0xEF);
    REQUIRE(gbb_peek_ram(machine, 0xC009) == 1);
    REQUIRE(gbb_peek_ram(machine, 0xC00A) == 7);
    REQUIRE(gbb_peek_ram(machine, 0xC00B) == 0);
    REQUIRE(gbb_peek_ram(machine, 0xC00C) == 0xFC);
    REQUIRE(gbb_peek_ram(machine, 0xC00D) == 0);
    REQUIRE(gbb_peek_ram(machine, 0xC00E) == 0);
    REQUIRE(gbb_peek_ram(machine, 0xC00F) == 0xFE);
    gbb_destroy(machine);
    return 0;
}

static int ppu_timing_partition(void) {
    guest_program p = {0};
    start_guest(&p);
    emit_reg(&p, 0x41, 0x20);
    const uint8_t halt[] = {0x76};
    gbb_instance *whole = load_guest_with_tail(&p, 0x91, halt, sizeof(halt));
    gbb_instance *parts = load_guest_with_tail(&p, 0x91, halt, sizeof(halt));
    REQUIRE(whole != NULL && parts != NULL);
    gbb_test_bus_event whole_bus[128], parts_bus[128];
    gbb_test_bus_event whole_ppu[1024], parts_ppu[1024];
    gbb_test_observer_set(whole, whole_bus, 128);
    gbb_test_observer_set(parts, parts_bus, 128);
    gbb_test_ppu_observer_set(whole, whole_ppu, 1024);
    gbb_test_ppu_observer_set(parts, parts_ppu, 1024);
    gbb_run_result run = gbb_run(whole, 2000, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    gbb_run_result setup_parts = gbb_run(parts, 2000, NULL, 0);
    REQUIRE(setup_parts.reason == GBB_STOP_HALTED_IDLE &&
            setup_parts.consumed_half_dots == run.consumed_half_dots);
    run = gbb_run(whole, 145000, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE && run.consumed_half_dots == 145000u);
    static const uint64_t partitions[] = {8, 16, 80, 912, 456, 1312, 10000, 12000,
                                          30000, 50000, 40216};
    uint64_t total = 0;
    for (size_t i = 0; i < sizeof(partitions) / sizeof(partitions[0]); ++i) {
        run = gbb_run(parts, partitions[i], NULL, 0);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE &&
                run.consumed_half_dots == partitions[i]);
        total += run.consumed_half_dots;
    }
    REQUIRE(total == 145000u);
    size_t whole_bus_count = gbb_test_observer_count(whole);
    size_t parts_bus_count = gbb_test_observer_count(parts);
    size_t whole_ppu_count = gbb_test_ppu_observer_count(whole);
    size_t parts_ppu_count = gbb_test_ppu_observer_count(parts);
    REQUIRE(whole_bus_count == parts_bus_count);
    REQUIRE(memcmp(whole_bus, parts_bus, whole_bus_count * sizeof(*whole_bus)) == 0);
    REQUIRE(whole_ppu_count == parts_ppu_count);
    REQUIRE(memcmp(whole_ppu, parts_ppu, whole_ppu_count * sizeof(*whole_ppu)) == 0);
    const gbb_test_bus_event *enable = find_bus_event(whole_bus, whole_bus_count,
                                                       0xFF40, 2, 0x91);
    REQUIRE(enable != NULL);
    const gbb_test_bus_event *vblank = find_ppu_event(whole_ppu, whole_ppu_count,
                                                       7, -1,
                                                       enable->time_half_dots);
    const gbb_test_bus_event *ly_wrap = find_ppu_event(whole_ppu, whole_ppu_count,
                                                        6, 0,
                                                        enable->time_half_dots + 1u);
    REQUIRE(vblank != NULL && ly_wrap != NULL);
    REQUIRE((vblank->value & 1u) != 0);
    REQUIRE(vblank->time_half_dots - enable->time_half_dots == 144u * 912u);
    REQUIRE(ly_wrap->time_half_dots - enable->time_half_dots == 154u * 912u);
    uint8_t whole_frame[PIXELS], parts_frame[PIXELS];
    gbb_frame_info whole_info = {0}, parts_info = {0};
    REQUIRE(gbb_copy_frame(whole, whole_frame, PIXELS, WIDTH, &whole_info) == GBB_OK);
    REQUIRE(gbb_copy_frame(parts, parts_frame, PIXELS, WIDTH, &parts_info) == GBB_OK);
    REQUIRE(whole_info.generation == parts_info.generation);
    REQUIRE(whole_info.completion_half_dots == parts_info.completion_half_dots);
    REQUIRE(whole_info.completion_half_dots == vblank->time_half_dots);
    REQUIRE(memcmp(whole_frame, parts_frame, sizeof(whole_frame)) == 0);
    /* A budget too small for the next instruction must leave device time untouched. */
    guest_program live = {0};
    start_guest(&live);
    gbb_instance *short_budget = load_guest(&live, 0x91);
    REQUIRE(short_budget != NULL);
    gbb_test_bus_event short_ppu[64];
    gbb_test_ppu_observer_set(short_budget, short_ppu, 64);
    run = gbb_run(short_budget, 1, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 0);
    REQUIRE(gbb_test_ppu_observer_count(short_budget) == 0);
    gbb_destroy(short_budget);

    /* VBlank is visible through IF, and the guest-visible LY register wraps after line 153. */
    memset(&p, 0, sizeof(p));
    start_guest(&p);
    const uint8_t poll_if[] = {0xF0, 0x0F, 0xEA, 0x10, 0xC0, 0x18, 0xF9};
    gbb_instance *interrupt_guest = load_guest_with_tail(&p, 0x91, poll_if,
                                                          sizeof(poll_if));
    REQUIRE(interrupt_guest != NULL);
    run = gbb_run(interrupt_guest, 132000, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE((gbb_peek_ram(interrupt_guest, 0xC010) & 1u) != 0);
    gbb_destroy(interrupt_guest);

    memset(&p, 0, sizeof(p));
    start_guest(&p);
    const uint8_t poll_ly[] = {0xF0, 0x44, 0xEA, 0x11, 0xC0, 0x18, 0xF9};
    gbb_instance *ly_guest = load_guest_with_tail(&p, 0x91, poll_ly,
                                                   sizeof(poll_ly));
    REQUIRE(ly_guest != NULL);
    run = gbb_run(ly_guest, 141000, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(ly_guest, 0xC011) == 0);
    gbb_destroy(ly_guest);
    gbb_destroy(whole);
    gbb_destroy(parts);
    return 0;
}

static int frame_copy_failures(void) {
    guest_program p = {0};
    start_guest(&p);
    gbb_instance *machine = load_guest(&p, 0x91);
    gbb_instance *control = load_guest(&p, 0x91);
    REQUIRE(machine != NULL && control != NULL);

    uint8_t pixels[PIXELS];
    uint8_t pixels_before[sizeof(pixels)];
    memset(pixels, 0xA5, sizeof(pixels));
    memcpy(pixels_before, pixels, sizeof(pixels));
    gbb_frame_info info;
    gbb_frame_info info_before;
    memset(&info, 0x5A, sizeof(info));
    memcpy(&info_before, &info, sizeof(info));

    REQUIRE(gbb_copy_frame(NULL, pixels, sizeof(pixels), WIDTH, &info) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_frame(machine, NULL, sizeof(pixels), WIDTH, &info) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), WIDTH, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), WIDTH - 1u, &info) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels) - 1u, WIDTH, &info) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_frame(machine, pixels, SIZE_MAX, SIZE_MAX, &info) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), WIDTH, &info) == GBB_FRAME_NOT_READY);
    REQUIRE(memcmp(pixels, pixels_before, sizeof(pixels)) == 0);
    REQUIRE(memcmp(&info, &info_before, sizeof(info)) == 0);

    gbb_run_result subject_run = gbb_run(machine, UINT64_C(145000), NULL, 0);
    gbb_run_result control_run = gbb_run(control, UINT64_C(145000), NULL, 0);
    REQUIRE(subject_run.reason == GBB_STOP_BUDGET && control_run.reason == GBB_STOP_BUDGET);
    REQUIRE(subject_run.consumed_half_dots == control_run.consumed_half_dots);

    union {
        max_align_t alignment;
        gbb_frame_info info;
        uint8_t pixels[PIXELS];
    } overlap;
    memset(&overlap, 0x3C, sizeof(overlap));
    gbb_frame_info *overlap_info = &overlap.info;
    uint8_t overlap_before[sizeof(overlap)];
    memcpy(overlap_before, &overlap, sizeof(overlap));
    REQUIRE(gbb_copy_frame(machine, overlap.pixels, sizeof(overlap.pixels), WIDTH,
                           overlap_info) == GBB_INVALID_ARGUMENT);
    REQUIRE(memcmp(&overlap, overlap_before, sizeof(overlap)) == 0);

    uint8_t actual[PIXELS], expected[PIXELS];
    gbb_frame_info actual_info = {0}, expected_info = {0};
    REQUIRE(gbb_copy_frame(machine, actual, sizeof(actual), WIDTH, &actual_info) == GBB_OK);
    REQUIRE(gbb_copy_frame(control, expected, sizeof(expected), WIDTH, &expected_info) == GBB_OK);
    REQUIRE(memcmp(actual, expected, sizeof(actual)) == 0);
    REQUIRE(actual_info.width == expected_info.width && actual_info.height == expected_info.height);
    REQUIRE(actual_info.generation == expected_info.generation);
    REQUIRE(actual_info.completion_half_dots == expected_info.completion_half_dots);
    gbb_destroy(machine);
    gbb_destroy(control);
    return 0;
}

static int frame_generation_lifecycle(void) {
    guest_program p = {0};
    start_guest(&p);
    gbb_instance *machine = load_guest(&p, 0x91);
    REQUIRE(machine != NULL);

    enum { PAD = 3u, PITCH = WIDTH + PAD,
           REQUIRED = (HEIGHT - 1u) * PITCH + WIDTH };
    uint8_t guarded[REQUIRED + PAD + 2u];
    memset(guarded, 0xA5, sizeof(guarded));
    uint8_t guarded_before[sizeof(guarded)];
    memcpy(guarded_before, guarded, sizeof(guarded));
    gbb_frame_info info;
    gbb_frame_info info_before;
    memset(&info, 0x5A, sizeof(info));
    memcpy(&info_before, &info, sizeof(info));
    REQUIRE(gbb_copy_frame(machine, guarded + 1u, REQUIRED, PITCH, &info) == GBB_FRAME_NOT_READY);
    REQUIRE(memcmp(guarded, guarded_before, sizeof(guarded)) == 0);
    REQUIRE(memcmp(&info, &info_before, sizeof(info)) == 0);

    gbb_run_result run = gbb_run(machine, UINT64_C(145000), NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_copy_frame(machine, guarded + 1u, REQUIRED, PITCH, &info) == GBB_OK);
    REQUIRE(info.width == WIDTH && info.height == HEIGHT && info.generation > 0);
    REQUIRE(guarded[0] == 0xA5 && guarded[sizeof(guarded) - 1u] == 0xA5);
    for (size_t y = 0; y < HEIGHT; ++y) {
        for (size_t x = 0; x < WIDTH; ++x)
            REQUIRE(guarded[1u + y * PITCH + x] <= 3u);
        for (size_t x = WIDTH; x < PITCH; ++x)
            REQUIRE(guarded[1u + y * PITCH + x] == 0xA5);
    }

    uint8_t repeated[PIXELS];
    gbb_frame_info repeated_info = {0};
    REQUIRE(gbb_copy_frame(machine, repeated, sizeof(repeated), WIDTH, &repeated_info) == GBB_OK);
    REQUIRE(repeated_info.generation == info.generation);
    REQUIRE(repeated_info.completion_half_dots == info.completion_half_dots);
    for (size_t y = 0; y < HEIGHT; ++y)
        REQUIRE(memcmp(guarded + 1u + y * PITCH, repeated + y * WIDTH, WIDTH) == 0);

    run = gbb_run(machine, 912, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 912);
    gbb_frame_info partial_info = {0};
    REQUIRE(gbb_copy_frame(machine, repeated, sizeof(repeated), WIDTH, &partial_info) == GBB_OK);
    REQUIRE(partial_info.generation == info.generation);
    REQUIRE(partial_info.completion_half_dots == info.completion_half_dots);
    for (size_t y = 0; y < HEIGHT; ++y)
        REQUIRE(memcmp(guarded + 1u + y * PITCH, repeated + y * WIDTH, WIDTH) == 0);

    REQUIRE(gbb_reset(machine) == GBB_OK);
    memset(repeated, 0xB6, sizeof(repeated));
    uint8_t repeated_before[sizeof(repeated)];
    memcpy(repeated_before, repeated, sizeof(repeated));
    memset(&partial_info, 0xC7, sizeof(partial_info));
    gbb_frame_info reset_info_before;
    memcpy(&reset_info_before, &partial_info, sizeof(partial_info));
    REQUIRE(gbb_copy_frame(machine, repeated, sizeof(repeated), WIDTH, &partial_info) == GBB_FRAME_NOT_READY);
    REQUIRE(memcmp(repeated, repeated_before, sizeof(repeated)) == 0);
    REQUIRE(memcmp(&partial_info, &reset_info_before, sizeof(partial_info)) == 0);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "frame_composition_bg") == 0) return frame_composition_bg();
    if (strcmp(argv[1], "frame_composition_window") == 0) return frame_composition_window();
    if (strcmp(argv[1], "frame_composition_sprites") == 0) return frame_composition_sprites();
    if (strcmp(argv[1], "frame_composition_priority") == 0) return frame_composition_priority();
    if (strcmp(argv[1], "ppu_timing_modes") == 0) return ppu_timing_modes();
    if (strcmp(argv[1], "ppu_timing_stat") == 0) return ppu_timing_stat();
    if (strcmp(argv[1], "ppu_timing_lcd") == 0) return ppu_timing_lcd();
    if (strcmp(argv[1], "ppu_timing_fetch") == 0) return ppu_timing_fetch();
    if (strcmp(argv[1], "ppu_timing_partition") == 0) return ppu_timing_partition();
    if (strcmp(argv[1], "frame_copy_failures") == 0) return frame_copy_failures();
    if (strcmp(argv[1], "frame_generation_lifecycle") == 0) return frame_generation_lifecycle();
    return 2;
}
