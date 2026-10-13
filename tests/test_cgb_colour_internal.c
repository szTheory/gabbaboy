/* White-box colour checks (Phase 11, D-25, D-35 stage 1). This is a single translation unit that
 * includes the core source, so it must not link GabbaBoy::core. The mutant harness
 * (gbb_colour_mutant in tests/CMakeLists.txt) swaps the included core for a build-tree copy with
 * one source anchor rewritten, through the GBB_COLOUR_CORE_SOURCE seam below.
 *
 * Usage: test_cgb_colour_internal <case> [fixtures-root] */
#ifdef GBB_COLOUR_CORE_SOURCE
#include GBB_COLOUR_CORE_SOURCE
#else
#include "../src/core/gabbaboy.c"
#endif

#include <stdio.h>
#include <stdlib.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define FRAME_HALF_DOTS 140448u

static uint64_t fnv1a64(const uint8_t *data, size_t size) {
    uint64_t h = UINT64_C(0xCBF29CE484222325);
    for (size_t i = 0; i < size; ++i) {
        h ^= data[i];
        h *= UINT64_C(0x100000001B3);
    }
    return h;
}

static uint8_t *read_file(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long n = ftell(f);
    if (n <= 0 || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    uint8_t *buffer = malloc((size_t)n);
    if (buffer == NULL || fread(buffer, 1, (size_t)n, f) != (size_t)n) {
        free(buffer);
        fclose(f);
        return NULL;
    }
    fclose(f);
    *size = (size_t)n;
    return buffer;
}

/* Regression pins recorded from the unmodified pre-phase-11 core at the head that opened the
 * phase. They are not hardware evidence: they only prove the DMG shade path did not move. */
typedef struct {
    const char *path;
    unsigned frames;
    uint64_t digest;
} shade_pin;

/* libbet draws nothing for its first several hundred frames, so it runs 900 frames to reach its
 * title graphics. The tracer ROM renders a blank (all shade 0) frame: its pin guards that the
 * blank stays blank. The demo carries a small non-zero patch. */
static const shade_pin SHADE_PINS[] = {
    {"visible-demo/demo.gb", 60u, UINT64_C(0x9b2cc3b0e3625f65)},
    {"libbet/libbet.gb", 900u, UINT64_C(0xccfe17f6b26fd21d)},
    {"tracer/tracer.gb", 60u, UINT64_C(0xeca47f6549902b25)},
};

static int cgb_dmg_identity_shade_pin(const char *root) {
    int failed = 0;
    for (size_t i = 0; i < sizeof(SHADE_PINS) / sizeof(SHADE_PINS[0]); ++i) {
        char path[1024];
        snprintf(path, sizeof(path), "%s/%s", root, SHADE_PINS[i].path);
        size_t size = 0;
        uint8_t *rom = read_file(path, &size);
        REQUIRE(rom != NULL);
        gbb_instance *m = NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
        REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
        for (unsigned f = 0; f < SHADE_PINS[i].frames; ++f) {
            gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
            REQUIRE(r.reason == GBB_STOP_BUDGET || r.reason == GBB_STOP_HALTED_IDLE);
        }
        uint64_t digest = fnv1a64(m->frame_completed, sizeof(m->frame_completed));
        if (digest != SHADE_PINS[i].digest) {
            fprintf(stderr, "observed %s %016llx\n", SHADE_PINS[i].path,
                    (unsigned long long)digest);
            failed = 1;
        }
        gbb_destroy(m);
        free(rom);
    }
    return failed;
}

/* Control case for the mutant harness: only constructs and destroys an instance. */
static int cgb_colour_internal_harness_alive(void) {
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    gbb_destroy(m);
    return 0;
}

/* D-22 truth table: rows are the independent Python oracle's output (GB-CPU-002), never derived
 * from the core. Fields follow the header in the .inc file. */
typedef struct {
    uint8_t mode, lcdc0, bg_attr7, bg_index, a_index, a_pri, b_index, b_pri, order;
    uint8_t expect_layer, expect_index;
} priority_row;

static const priority_row PRIORITY_ROWS[] = {
#include "data/cgb-priority-truth.inc"
};

static const priority_row *find_row(const priority_row *want_inputs) {
    for (size_t i = 0; i < sizeof(PRIORITY_ROWS) / sizeof(PRIORITY_ROWS[0]); ++i) {
        const priority_row *r = &PRIORITY_ROWS[i];
        if (r->mode == want_inputs->mode && r->lcdc0 == want_inputs->lcdc0 &&
            r->bg_attr7 == want_inputs->bg_attr7 && r->bg_index == want_inputs->bg_index &&
            r->a_index == want_inputs->a_index && r->a_pri == want_inputs->a_pri &&
            r->b_index == want_inputs->b_index && r->b_pri == want_inputs->b_pri &&
            r->order == want_inputs->order)
            return r;
    }
    return NULL;
}

/* Hand-written golden rows, each quoting the Pan Docs rule it exercises. Layer: 0 BG, 1 A, 2 B. */
static const priority_row GOLDEN_ROWS[] = {
    /* CGB: LCDC.0 = 0 removes all BG priority, so an opaque object wins over BG index 3 even with
     * OAM bit 7 and BG attribute bit 7 set. */
    {0, 0, 1, 3, 2, 1, 0, 0, 1, 1, 2},
    /* CGB: LCDC.0 = 1 and BG attribute bit 7 set keeps BG index 1-3 in front of the object. */
    {0, 1, 1, 1, 2, 0, 0, 0, 1, 0, 1},
    /* BG colour index 0 never hides an object, whatever the priority bits say. */
    {0, 1, 1, 0, 2, 1, 0, 0, 1, 1, 2},
    /* CGB objects order by OAM index only, but a transparent A leaves B as the candidate. */
    {0, 1, 0, 0, 0, 0, 3, 0, 2, 2, 3},
    /* Compat: LCDC.0 = 0 blanks the BG (index 0) and no opaque object leaves the BG shown. */
    {1, 0, 0, 3, 0, 0, 0, 0, 1, 0, 0},
    /* Compat: BG map attribute bit 7 is ignored; with OAM bit 7 clear the object wins. */
    {1, 1, 1, 2, 1, 0, 0, 0, 1, 1, 1},
    /* Compat: objects order by X, so the lower X (B) wins when A.x is greater. */
    {1, 1, 0, 0, 1, 0, 2, 0, 2, 2, 2},
    /* Compat: equal X falls back to the lower OAM index (A). */
    {1, 1, 0, 0, 1, 0, 2, 0, 1, 1, 1},
};

static int cgb_priority_table_shape(void) {
    enum { ROWS = 2 * 2 * 2 * 4 * 8 * 8 * 3 };
    static uint8_t seen[ROWS];
    size_t count = sizeof(PRIORITY_ROWS) / sizeof(PRIORITY_ROWS[0]);
    REQUIRE(GBB_CGB_PRIORITY_TRUTH_ROWS == 6144);
    REQUIRE(count == GBB_CGB_PRIORITY_TRUTH_ROWS);
    REQUIRE(count == (size_t)ROWS);
    for (size_t i = 0; i < count; ++i) {
        const priority_row *r = &PRIORITY_ROWS[i];
        REQUIRE(r->mode < 2 && r->lcdc0 < 2 && r->bg_attr7 < 2 && r->bg_index < 4);
        REQUIRE(r->a_index < 4 && r->a_pri < 2 && r->b_index < 4 && r->b_pri < 2 && r->order < 3);
        REQUIRE(r->expect_layer < 3 && r->expect_index < 4);
        size_t key = r->mode;
        key = key * 2u + r->lcdc0;
        key = key * 2u + r->bg_attr7;
        key = key * 4u + r->bg_index;
        key = key * 8u + (size_t)(r->a_index * 2u + r->a_pri);
        key = key * 8u + (size_t)(r->b_index * 2u + r->b_pri);
        key = key * 3u + r->order;
        REQUIRE(key < (size_t)ROWS);
        REQUIRE(seen[key] == 0u);
        seen[key] = 1u;
    }
    for (size_t i = 0; i < sizeof(GOLDEN_ROWS) / sizeof(GOLDEN_ROWS[0]); ++i) {
        const priority_row *row = find_row(&GOLDEN_ROWS[i]);
        if (row == NULL || row->expect_layer != GOLDEN_ROWS[i].expect_layer ||
            row->expect_index != GOLDEN_ROWS[i].expect_index) {
            fprintf(stderr, "golden row %zu disagrees with the truth table\n", i);
            return 1;
        }
    }
    return 0;
}


/* ---- Palette RAM ports (Phase 11 plan 11-02; D-08, D-10 to D-14) ----------------------------------
 * These cases drive read8/write8 directly with lcdc and ppu_mode set by hand, so each lock state is
 * exact. Expected bytes come from the decisions, not from the core. */
static gbb_instance *make_machine(int cgb_mode) {
    static uint8_t rom[0x8000];
    memset(rom, 0, sizeof(rom));
    rom[0x101] = 0xC3u; rom[0x102] = 0x50u; rom[0x103] = 0x01u;
    rom[0x143] = cgb_mode ? 0x80u : 0x00u;
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &m) != GBB_OK || gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(m);
        return NULL;
    }
    m->lcdc = 0x91u;   /* LCD on ... */
    m->ppu_mode = 0u;  /* ... in HBlank, where the CPU may reach CRAM */
    return m;
}

#define BCPS 0xFF68u
#define BCPD 0xFF69u
#define OCPS 0xFF6Au
#define OCPD 0xFF6Bu
#define OPRI_PORT 0xFF6Cu

static int palette_cram_bg_autoinc(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    write8(m, BCPS, 0x80u);
    uint8_t seq[64];
    int saw_bit7 = 0;
    for (unsigned i = 0; i < 64u; ++i) {
        seq[i] = (uint8_t)(i * 5u + 0x83u); /* all 8 bits of each byte are kept */
        saw_bit7 |= (seq[i] & 0x80u) != 0u;
        write8(m, BCPD, seq[i]);
        if (i == 0u) REQUIRE(read8(m, BCPS) == 0xC1u);
    }
    REQUIRE(saw_bit7);
    for (unsigned i = 0; i < 64u; ++i) REQUIRE(m->bg_cram[i] == seq[i]);
    REQUIRE(read8(m, BCPS) == 0xC0u); /* wrapped 63 to 0, bit 7 kept, bit 6 reads 1 */
    gbb_destroy(m);
    return 0;
}

static int palette_cram_bg_readback(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    write8(m, BCPS, 0x03u);
    write8(m, BCPD, 0x6Bu); /* bit 7 clear: no increment */
    REQUIRE(read8(m, BCPS) == 0x43u);
    REQUIRE(read8(m, BCPD) == 0x6Bu);
    REQUIRE(read8(m, BCPD) == 0x6Bu);
    REQUIRE(read8(m, BCPS) == 0x43u);
    write8(m, BCPS, 0x83u); /* bit 7 set: reads still never advance the index */
    REQUIRE(read8(m, BCPD) == 0x6Bu);
    REQUIRE(read8(m, BCPD) == 0x6Bu);
    REQUIRE(read8(m, BCPS) == 0xC3u);
    gbb_destroy(m);
    return 0;
}

static int palette_cram_bg_blocked_write(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    write8(m, BCPS, 0x05u);
    write8(m, BCPD, 0x34u);
    REQUIRE(m->bg_cram[5] == 0x34u);
    m->ppu_mode = 3u; /* LCD on, pixel transfer: the write is blocked */
    write8(m, BCPS, 0x85u);
    write8(m, BCPD, 0x12u);
    REQUIRE(m->bg_cram[5] == 0x34u);
    REQUIRE(read8(m, BCPS) == 0xC6u); /* the index still advanced */
    gbb_destroy(m);
    return 0;
}

static int palette_cram_bg_blocked_read(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    write8(m, BCPS, 0x07u);
    write8(m, BCPD, 0x77u);
    write8(m, BCPS, 0x87u);
    m->ppu_mode = 3u;
    REQUIRE(read8(m, BCPD) == 0xFFu);
    REQUIRE(read8(m, BCPS) == 0xC7u); /* a blocked read does not advance either */
    m->ppu_mode = 0u;
    REQUIRE(read8(m, BCPD) == 0x77u);
    gbb_destroy(m);
    return 0;
}

static int palette_cram_lockout_lcd_off(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    m->lcdc = 0x11u; /* LCD off: ppu_mode is stale, the lock does not apply */
    m->ppu_mode = 3u;
    write8(m, BCPS, 0x00u);
    write8(m, BCPD, 0x12u);
    REQUIRE(m->bg_cram[0] == 0x12u);
    REQUIRE(read8(m, BCPD) == 0x12u);
    /* LCD on, every mode except 3 allows the access. */
    m->lcdc = 0x91u;
    for (unsigned mode = 0; mode < 4u; ++mode) {
        m->ppu_mode = (uint8_t)mode;
        write8(m, BCPS, 0x01u);
        m->bg_cram[1] = 0u;
        write8(m, BCPD, 0x5Au);
        REQUIRE((m->bg_cram[1] == 0x5Au) == (mode != 3u));
    }
    gbb_destroy(m);
    return 0;
}

typedef struct {
    const char *name;
    int (*run)(void);
} plain_case;

static const plain_case PLAIN_CASES[] = {
    {"palette_cram_bg_autoinc", palette_cram_bg_autoinc},
    {"palette_cram_bg_readback", palette_cram_bg_readback},
    {"palette_cram_bg_blocked_write", palette_cram_bg_blocked_write},
    {"palette_cram_bg_blocked_read", palette_cram_bg_blocked_read},
    {"palette_cram_lockout_lcd_off", palette_cram_lockout_lcd_off},
};

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (strcmp(argv[1], "cgb_colour_internal_harness_alive") == 0)
        return cgb_colour_internal_harness_alive() == 0 ? (puts("cgb-colour-internal cgb_colour_internal_harness_alive pass"), 0) : 1;
    if (strcmp(argv[1], "cgb_dmg_identity_shade_pin") == 0) {
        if (argc != 3) return 2;
        int rc = cgb_dmg_identity_shade_pin(argv[2]);
        if (rc == 0) puts("cgb-colour-internal cgb_dmg_identity_shade_pin pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_priority_table_shape") == 0) {
        int rc = cgb_priority_table_shape();
        if (rc == 0) puts("cgb-colour-internal cgb_priority_table_shape pass");
        return rc;
    }
    for (size_t i = 0; i < sizeof(PLAIN_CASES) / sizeof(PLAIN_CASES[0]); ++i) {
        if (strcmp(argv[1], PLAIN_CASES[i].name) != 0) continue;
        int rc = PLAIN_CASES[i].run();
        if (rc == 0) printf("cgb-colour-internal %s pass\n", PLAIN_CASES[i].name);
        return rc;
    }
    return 2;
}
