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


/* ---- Task 2: catch-up, corruption matrix and generation rules ---- */

#define IMG (8192u + BLOCK)

static const uint8_t *block_of(const uint8_t *image) { return image + 8192u; }

static int snapshot(const gbb_instance *m, uint8_t *image, uint64_t *generation) {
    size_t size = 0u;
    if (!export_image(m, image, IMG, &size) || size != IMG) return 0;
    return gbb_battery_generation(m, generation) == GBB_OK;
}

static int rtc_catch_up_basic(void) {
    gbb_instance *m = load_idle(0x10u, 0x02u);
    REQUIRE(m != NULL);
    REQUIRE(gbb_rtc_catch_up(m, 3661) == GBB_OK);
    uint8_t image[IMG];
    uint64_t gen = 0u;
    REQUIRE(snapshot(m, image, &gen));
    REQUIRE(block_of(image)[9] == 1u && block_of(image)[10] == 1u && block_of(image)[11] == 1u);
    REQUIRE(gen == 1u);
    gbb_destroy(m);
    return 0;
}

static int rtc_catch_up_zero(void) {
    gbb_instance *m = load_idle(0x10u, 0x02u);
    REQUIRE(m != NULL);
    uint8_t before[IMG], after[IMG];
    uint64_t g0 = 0u, g1 = 0u;
    REQUIRE(snapshot(m, before, &g0));
    REQUIRE(gbb_rtc_catch_up(m, 0) == GBB_OK);
    REQUIRE(snapshot(m, after, &g1));
    REQUIRE(g0 == g1);
    REQUIRE(memcmp(before, after, IMG) == 0);
    gbb_destroy(m);
    return 0;
}

static int rtc_catch_up_negative(void) {
    gbb_instance *m = load_idle(0x10u, 0x02u);
    REQUIRE(m != NULL);
    uint8_t before[IMG], after[IMG];
    uint64_t g0 = 0u, g1 = 0u;
    REQUIRE(snapshot(m, before, &g0));
    REQUIRE(gbb_rtc_catch_up(m, -1) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_rtc_catch_up(m, INT64_MIN) == GBB_INVALID_ARGUMENT);
    REQUIRE(snapshot(m, after, &g1));
    REQUIRE(g0 == g1 && memcmp(before, after, IMG) == 0);
    gbb_destroy(m);
    return 0;
}

static int rtc_catch_up_int64_max(void) {
    gbb_instance *m = load_idle(0x10u, 0x02u);
    REQUIRE(m != NULL);
    REQUIRE(gbb_rtc_catch_up(m, INT64_MAX) == GBB_OK);
    /* Closed form from zero: S, M, H are mixed-radix digits, the rest is days. */
    const uint64_t secs = (uint64_t)INT64_MAX;
    const uint64_t mins = secs / 60u, hours = mins / 60u, days = hours / 24u;
    uint8_t image[IMG];
    uint64_t gen = 0u;
    REQUIRE(snapshot(m, image, &gen));
    const uint8_t *b = block_of(image);
    REQUIRE(b[9] == (uint8_t)(secs % 60u));
    REQUIRE(b[10] == (uint8_t)(mins % 60u));
    REQUIRE(b[11] == (uint8_t)(hours % 24u));
    REQUIRE(b[12] == (uint8_t)(days & 0xFFu));
    REQUIRE(b[13] == (uint8_t)(((days >> 8) & 1u) | (days >= 512u ? 0x80u : 0u)));
    gbb_destroy(m);
    return 0;
}

/* Guest writes DH = value (halt/carry/day bit) and optional day-low, then spins. */
static gbb_instance *load_with_registers(uint8_t dl, uint8_t dh) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0x4000u, 0x0Bu);
    emit_write(&p, 0xA000u, dl);
    emit_write(&p, 0x4000u, 0x0Cu);
    emit_write(&p, 0xA000u, dh);
    emit_spin(&p);
    gbb_instance *m = load_type(0x10u, 0x02u, &p);
    if (m != NULL && !run_for(m, 20000u)) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

static int rtc_catch_up_halted(void) {
    gbb_instance *m = load_with_registers(0u, 0x40u);
    REQUIRE(m != NULL);
    uint8_t before[IMG], after[IMG];
    uint64_t g0 = 0u, g1 = 0u;
    REQUIRE(snapshot(m, before, &g0));
    REQUIRE(block_of(before)[13] == 0x40u);
    REQUIRE(gbb_rtc_catch_up(m, 123456) == GBB_OK);
    REQUIRE(snapshot(m, after, &g1));
    REQUIRE(g0 == g1 && memcmp(before, after, IMG) == 0);
    gbb_destroy(m);
    return 0;
}

static int rtc_catch_up_carry_sticky(void) {
    gbb_instance *m = load_with_registers(0xFFu, 0x01u); /* day 511 */
    REQUIRE(m != NULL);
    REQUIRE(gbb_rtc_catch_up(m, 86400) == GBB_OK);
    uint8_t image[IMG];
    uint64_t gen = 0u;
    REQUIRE(snapshot(m, image, &gen));
    REQUIRE(block_of(image)[12] == 0u);
    REQUIRE(block_of(image)[13] == 0x80u);
    REQUIRE(gbb_rtc_catch_up(m, 90000) == GBB_OK);
    REQUIRE(snapshot(m, image, &gen));
    REQUIRE((block_of(image)[13] & 0x80u) != 0u);
    REQUIRE(block_of(image)[12] == 1u);
    gbb_destroy(m);
    return 0;
}

static int rtc_catch_up_composes(void) {
    static const int64_t pairs[][3][2] = {
        /* each row: first machine a then b; twin applies c1 then c2 with the same sum */
        {{100000, 250000}, {350000, 0}, {0, 0}},
        {{INT64_MAX, INT64_MAX}, {INT64_MAX - 1000, 1000}, {INT64_MAX, 0}},
    };
    for (size_t i = 0u; i < 2u; ++i) {
        gbb_instance *a = load_idle(0x10u, 0x02u);
        gbb_instance *b = load_idle(0x10u, 0x02u);
        REQUIRE(a != NULL && b != NULL);
        REQUIRE(gbb_rtc_catch_up(a, pairs[i][0][0]) == GBB_OK);
        REQUIRE(gbb_rtc_catch_up(a, pairs[i][0][1]) == GBB_OK);
        REQUIRE(gbb_rtc_catch_up(b, pairs[i][1][0]) == GBB_OK);
        if (pairs[i][1][1] != 0) REQUIRE(gbb_rtc_catch_up(b, pairs[i][1][1]) == GBB_OK);
        if (pairs[i][2][0] != 0) REQUIRE(gbb_rtc_catch_up(b, pairs[i][2][0]) == GBB_OK);
        uint8_t ia[IMG], ib[IMG];
        uint64_t ga = 0u, gb = 0u;
        REQUIRE(snapshot(a, ia, &ga) && snapshot(b, ib, &gb));
        REQUIRE(memcmp(ia, ib, IMG) == 0);
        gbb_destroy(a);
        gbb_destroy(b);
    }
    return 0;
}

static int rtc_catch_up_preserves(void) {
    program p = roundtrip_program();
    gbb_instance *a = load_type(0x10u, 0x02u, &p);
    gbb_instance *b = load_type(0x10u, 0x02u, &p);
    REQUIRE(a != NULL && b != NULL);
    REQUIRE(run_for(a, 3u * HALF_DOTS_PER_SECOND / 2u));
    REQUIRE(run_for(b, 3u * HALF_DOTS_PER_SECOND / 2u));
    REQUIRE(gbb_rtc_catch_up(a, 5000) == GBB_OK);
    REQUIRE(run_for(a, 1000000u));
    REQUIRE(run_for(b, 1000000u));
    uint8_t ia[IMG], ib[IMG];
    uint64_t ga = 0u, gb = 0u;
    REQUIRE(snapshot(a, ia, &ga) && snapshot(b, ib, &gb));
    /* sub-second remainder and latched registers are identical; only live fields moved */
    REQUIRE(memcmp(block_of(ia) + 5, block_of(ib) + 5, 4u) == 0);
    REQUIRE(memcmp(block_of(ia) + 14, block_of(ib) + 14, 7u) == 0);
    REQUIRE(memcmp(block_of(ia) + 9, block_of(ib) + 9, 3u) != 0);
    REQUIRE(ga == gb + 1u);
    gbb_destroy(a);
    gbb_destroy(b);
    return 0;
}

static int rtc_catch_up_errors(void) {
    REQUIRE(gbb_rtc_catch_up(NULL, 1) == GBB_INVALID_ARGUMENT);
    gbb_instance *empty = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &empty) == GBB_OK);
    REQUIRE(gbb_rtc_catch_up(empty, 1) == GBB_NO_RTC);
    gbb_destroy(empty);
    static const uint8_t types[][2] = {{0x01u, 0x00u}, {0x03u, 0x02u}, {0x11u, 0x00u},
                                       {0x12u, 0x02u}, {0x13u, 0x02u}, {0x19u, 0x00u}};
    /* $13 has a battery but no timer */
    for (size_t i = 0u; i < sizeof(types) / sizeof(types[0]); ++i) {
        gbb_instance *m = load_idle(types[i][0], types[i][1]);
        REQUIRE(m != NULL);
        REQUIRE(gbb_rtc_catch_up(m, 1) == GBB_NO_RTC);
        REQUIRE(gbb_rtc_catch_up(m, -1) == GBB_NO_RTC); /* the type check comes first */
        gbb_destroy(m);
    }
    return 0;
}

static int rtc_import_never_advances(void) {
    program p = roundtrip_program();
    gbb_instance *m = load_type(0x10u, 0x02u, &p);
    REQUIRE(m != NULL);
    REQUIRE(run_for(m, 5u * HALF_DOTS_PER_SECOND / 2u));
    uint8_t image[IMG], again[IMG];
    uint64_t gen = 0u;
    REQUIRE(snapshot(m, image, &gen));
    REQUIRE(run_for(m, 9u * HALF_DOTS_PER_SECOND / 2u));
    REQUIRE(gbb_import_battery(m, image, IMG) == GBB_OK);
    REQUIRE(snapshot(m, again, &gen));
    REQUIRE(memcmp(image, again, IMG) == 0);
    gbb_destroy(m);
    return 0;
}

typedef struct { size_t offset; uint8_t value; gbb_error expect; } mutation;

static int rtc_block_corruption_matrix(void) {
    program p = roundtrip_program();
    gbb_instance *m = load_type(0x10u, 0x02u, &p);
    REQUIRE(m != NULL);
    REQUIRE(run_for(m, 2u * HALF_DOTS_PER_SECOND));
    uint8_t good[IMG];
    uint64_t gen = 0u;
    REQUIRE(snapshot(m, good, &gen));
    const size_t o = 8192u;
    static const size_t copies[2] = {9u, 14u};
    mutation list[96];
    size_t n = 0u;
    for (size_t k = 0u; k < 4u; ++k) list[n++] = (mutation){o + k, (uint8_t)(good[o + k] ^ 0x01u), GBB_INVALID_ARGUMENT};
    list[n++] = (mutation){o + 4u, 0u, GBB_INVALID_ARGUMENT};
    list[n++] = (mutation){o + 4u, 2u, GBB_INVALID_ARGUMENT};
    list[n++] = (mutation){o + 4u, 255u, GBB_INVALID_ARGUMENT};
    list[n++] = (mutation){o + 7u, 0x80u, GBB_INVALID_ARGUMENT}; /* sub = 0x800000 */
    list[n++] = (mutation){o + 8u, 0xFFu, GBB_INVALID_ARGUMENT}; /* sub >= 2^24 */
    list[n++] = (mutation){o + 8u, 0x01u, GBB_INVALID_ARGUMENT};
    list[n++] = (mutation){o + 20u, 1u, GBB_INVALID_ARGUMENT};
    for (size_t c = 0u; c < 2u; ++c) {
        list[n++] = (mutation){o + copies[c] + 0u, 0x40u, GBB_INVALID_ARGUMENT};
        list[n++] = (mutation){o + copies[c] + 1u, 0x40u, GBB_INVALID_ARGUMENT};
        list[n++] = (mutation){o + copies[c] + 2u, 0x20u, GBB_INVALID_ARGUMENT};
        for (unsigned bit = 1u; bit <= 5u; ++bit)
            list[n++] = (mutation){o + copies[c] + 4u, (uint8_t)(1u << bit), GBB_INVALID_ARGUMENT};
    }
    for (size_t i = 0u; i < n; ++i) {
        uint8_t bad[IMG], after[IMG];
        uint64_t g1 = 0u;
        memcpy(bad, good, IMG);
        bad[list[i].offset] = list[i].value;
        REQUIRE(gbb_import_battery(m, bad, IMG) == list[i].expect);
        REQUIRE(snapshot(m, after, &g1));
        REQUIRE(g1 == gen && memcmp(after, good, IMG) == 0);
    }
    /* sub = 0xFFFFFFFF */
    {
        uint8_t bad[IMG], after[IMG];
        uint64_t g1 = 0u;
        memcpy(bad, good, IMG);
        memset(bad + o + 5u, 0xFF, 4u);
        REQUIRE(gbb_import_battery(m, bad, IMG) == GBB_INVALID_ARGUMENT);
        REQUIRE(snapshot(m, after, &g1));
        REQUIRE(g1 == gen && memcmp(after, good, IMG) == 0);
    }
    /* wrong lengths */
    {
        uint8_t big[IMG + 1u], after[IMG];
        uint64_t g1 = 0u;
        memset(big, 0, sizeof(big));
        memcpy(big, good, IMG);
        REQUIRE(gbb_import_battery(m, good, IMG - 1u) == GBB_BATTERY_SIZE_MISMATCH);
        REQUIRE(gbb_import_battery(m, big, IMG + 1u) == GBB_BATTERY_SIZE_MISMATCH);
        REQUIRE(snapshot(m, after, &g1));
        REQUIRE(g1 == gen && memcmp(after, good, IMG) == 0);
    }
    /* out-of-range-but-legal values import: S = 63, H = 31 in both copies */
    {
        uint8_t legal[IMG];
        memcpy(legal, good, IMG);
        for (size_t c = 0u; c < 2u; ++c) {
            legal[o + copies[c] + 0u] = 63u;
            legal[o + copies[c] + 2u] = 31u;
        }
        REQUIRE(gbb_import_battery(m, legal, IMG) == GBB_OK);
        uint8_t after[IMG];
        uint64_t g1 = 0u;
        REQUIRE(snapshot(m, after, &g1));
        REQUIRE(memcmp(after, legal, IMG) == 0);
    }
    gbb_destroy(m);
    return 0;
}

static int rtc_block_reset_roundtrip(void) {
    program p = roundtrip_program();
    gbb_instance *m = load_type(0x10u, 0x02u, &p);
    REQUIRE(m != NULL);
    REQUIRE(run_for(m, 2u * HALF_DOTS_PER_SECOND));
    uint8_t before[IMG], after[IMG];
    uint64_t gen = 0u;
    REQUIRE(snapshot(m, before, &gen));
    REQUIRE(gbb_reset(m) == GBB_OK);
    REQUIRE(snapshot(m, after, &gen));
    REQUIRE(memcmp(before, after, IMG) == 0);
    gbb_destroy(m);
    return 0;
}

static int rtc_block_generation(void) {
    program p = roundtrip_program();
    gbb_instance *m = load_type(0x10u, 0x02u, &p);
    REQUIRE(m != NULL);
    REQUIRE(run_for(m, 5u * HALF_DOTS_PER_SECOND / 2u));
    uint8_t image[IMG], again[IMG];
    uint64_t g0 = 0u, g1 = 0u;
    REQUIRE(snapshot(m, image, &g0));
    /* an identical import twice never bumps */
    REQUIRE(gbb_import_battery(m, image, IMG) == GBB_OK);
    REQUIRE(snapshot(m, again, &g1));
    REQUIRE(g1 == g0);
    REQUIRE(gbb_import_battery(m, image, IMG) == GBB_OK);
    REQUIRE(snapshot(m, again, &g1));
    REQUIRE(g1 == g0);
    /* a latch does not bump: a twin that latches ends at the same generation */
    program q = roundtrip_program();
    q.used -= 2u; /* drop the spin */
    emit_write(&q, 0x6000u, 0x00u);
    emit_write(&q, 0x6000u, 0x01u);
    emit_spin(&q);
    gbb_instance *latch = load_type(0x10u, 0x02u, &q);
    REQUIRE(latch != NULL);
    REQUIRE(run_for(latch, 5u * HALF_DOTS_PER_SECOND / 2u));
    uint64_t gl = 0u;
    REQUIRE(snapshot(latch, again, &gl));
    REQUIRE(gl == g0);
    /* catch-up bumps exactly once */
    REQUIRE(gbb_rtc_catch_up(m, 77) == GBB_OK);
    REQUIRE(snapshot(m, again, &g1));
    REQUIRE(g1 == g0 + 1u);
    gbb_destroy(latch);
    gbb_destroy(m);
    return 0;
}

static int rtc_battery_size_types(void) {
    static const struct { uint8_t type, ram; size_t size; int ok; } rows[] = {
        {0x0Fu, 0x00u, BLOCK, 1}, {0x10u, 0x02u, 8192u + BLOCK, 1},
        {0x10u, 0x03u, 32768u + BLOCK, 1}, {0x13u, 0x02u, 8192u, 1},
        {0x11u, 0x00u, 0u, 0}, {0x12u, 0x02u, 0u, 0}, {0x03u, 0x02u, 8192u, 1},
    };
    for (size_t i = 0u; i < sizeof(rows) / sizeof(rows[0]); ++i) {
        gbb_instance *m = load_idle(rows[i].type, rows[i].ram);
        REQUIRE(m != NULL);
        size_t size = 0u;
        if (rows[i].ok) {
            REQUIRE(gbb_battery_size(m, &size) == GBB_OK);
            REQUIRE(size == rows[i].size);
        } else {
            REQUIRE(gbb_battery_size(m, &size) == GBB_NO_BATTERY);
        }
        gbb_destroy(m);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    static const struct { const char *name; int (*fn)(void); } cases[] = {
        {"rtc_block_roundtrip", rtc_block_roundtrip},
        {"rtc_catch_up_basic", rtc_catch_up_basic},
        {"rtc_catch_up_zero", rtc_catch_up_zero},
        {"rtc_catch_up_negative", rtc_catch_up_negative},
        {"rtc_catch_up_int64_max", rtc_catch_up_int64_max},
        {"rtc_catch_up_halted", rtc_catch_up_halted},
        {"rtc_catch_up_carry_sticky", rtc_catch_up_carry_sticky},
        {"rtc_catch_up_composes", rtc_catch_up_composes},
        {"rtc_catch_up_preserves", rtc_catch_up_preserves},
        {"rtc_catch_up_errors", rtc_catch_up_errors},
        {"rtc_import_never_advances", rtc_import_never_advances},
        {"rtc_block_corruption_matrix", rtc_block_corruption_matrix},
        {"rtc_block_reset_roundtrip", rtc_block_reset_roundtrip},
        {"rtc_block_generation", rtc_block_generation},
        {"rtc_battery_size_types", rtc_battery_size_types},
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i)
        if (strcmp(argv[1], cases[i].name) == 0) return cases[i].fn();
    return 2;
}
