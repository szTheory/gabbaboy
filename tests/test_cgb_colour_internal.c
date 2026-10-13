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
    rom[0x150] = 0x18u; rom[0x151] = 0xFEu; /* jr $0150: an idle loop so rendering can run */
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


static int palette_cram_obj_autoinc(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    write8(m, OCPS, 0x80u);
    uint8_t seq[64];
    for (unsigned i = 0; i < 64u; ++i) {
        seq[i] = (uint8_t)(i * 7u + 0x91u);
        write8(m, OCPD, seq[i]);
    }
    for (unsigned i = 0; i < 64u; ++i) REQUIRE(m->obj_cram[i] == seq[i]);
    REQUIRE(read8(m, OCPS) == 0xC0u);
    /* The object side is independent of the background side. */
    write8(m, BCPS, 0x00u);
    write8(m, BCPD, 0x21u);
    REQUIRE(m->obj_cram[0] == seq[0]);
    REQUIRE(m->bg_cram[0] == 0x21u);
    /* Readback without increment, and a blocked write still advances the object index. */
    write8(m, OCPS, 0x84u);
    REQUIRE(read8(m, OCPD) == seq[4]);
    REQUIRE(read8(m, OCPS) == 0xC4u);
    m->ppu_mode = 3u;
    write8(m, OCPD, 0x00u);
    REQUIRE(m->obj_cram[4] == seq[4]);
    REQUIRE(read8(m, OCPS) == 0xC5u);
    gbb_destroy(m);
    return 0;
}

static int palette_cram_compat_ports(void) {
    gbb_instance *m = make_machine(0);
    REQUIRE(m != NULL);
    REQUIRE(m->exec_mode == GBB_MODE_CGB_DMG_COMPAT);
    write8(m, BCPS, 0x80u);
    write8(m, OCPS, 0x85u);
    uint8_t bg[64], obj[64];
    memcpy(bg, m->bg_cram, sizeof(bg));
    memcpy(obj, m->obj_cram, sizeof(obj));
    const uint8_t bcps = m->bcps, ocps = m->ocps;
    REQUIRE(read8(m, BCPD) == 0xFFu);
    REQUIRE(read8(m, OCPD) == 0xFFu);
    write8(m, BCPD, 0x12u);
    write8(m, OCPD, 0x34u);
    REQUIRE(memcmp(bg, m->bg_cram, sizeof(bg)) == 0);
    REQUIRE(memcmp(obj, m->obj_cram, sizeof(obj)) == 0);
    REQUIRE(m->bcps == bcps && m->ocps == ocps); /* no increment either */
    gbb_destroy(m);
    return 0;
}

static int palette_opri_cgb(void) {
    gbb_instance *m = make_machine(1);
    REQUIRE(m != NULL);
    REQUIRE(read8(m, OPRI_PORT) == 0xFEu);
    write8(m, OPRI_PORT, 0x01u);
    REQUIRE(read8(m, OPRI_PORT) == 0xFFu);
    write8(m, OPRI_PORT, 0x00u);
    REQUIRE(read8(m, OPRI_PORT) == 0xFEu);
    write8(m, OPRI_PORT, 0xFEu); /* only bit 0 is kept */
    REQUIRE(read8(m, OPRI_PORT) == 0xFEu);
    /* A write changes no other instance state: a whole-instance copy differs only in opri. */
    gbb_instance *before = malloc(sizeof(*before));
    REQUIRE(before != NULL);
    memcpy(before, m, sizeof(*before));
    write8(m, OPRI_PORT, 0x01u);
    REQUIRE(m->opri == 1u);
    before->opri = m->opri;
    REQUIRE(memcmp(before, m, sizeof(*before)) == 0);
    free(before);
    gbb_destroy(m);
    return 0;
}

static int palette_opri_compat(void) {
    gbb_instance *m = make_machine(0);
    REQUIRE(m != NULL);
    REQUIRE(read8(m, OPRI_PORT) == 0xFFu);
    write8(m, OPRI_PORT, 0x01u);
    REQUIRE(m->opri == 0u); /* the write was ignored, not stored */
    REQUIRE(read8(m, OPRI_PORT) == 0xFFu);
    gbb_destroy(m);
    return 0;
}

static int cram_is_white(const gbb_instance *m) {
    for (unsigned i = 0; i < sizeof(m->bg_cram); ++i) {
        const uint8_t want = (i & 1u) == 0u ? 0xFFu : 0x7Fu;
        if (m->bg_cram[i] != want || m->obj_cram[i] != want) return 0;
    }
    return 1;
}

static int cgb_postboot_cram_white(void) {
    for (int cgb_mode = 0; cgb_mode < 2; ++cgb_mode) {
        gbb_instance *m = make_machine(cgb_mode);
        REQUIRE(m != NULL);
        REQUIRE(cram_is_white(m));
        memset(m->bg_cram, 0, sizeof(m->bg_cram)); /* dirty, so reset has something to undo */
        memset(m->obj_cram, 0, sizeof(m->obj_cram));
        REQUIRE(!cram_is_white(m));
        REQUIRE(gbb_reset(m) == GBB_OK);
        REQUIRE(cram_is_white(m));
        gbb_destroy(m);
    }
    return 0;
}

static int vram1_is_zero(const gbb_instance *m) {
    for (unsigned i = 0; i < GBB_VRAM_BANK_SIZE; ++i)
        if (m->vram[1][i] != 0u) return 0;
    return 1;
}

/* D-40: attribute tests rely on VRAM bank 1 being zero after every load and reset. */
static int cgb_postboot_vram1_zero(void) {
    for (int cgb_mode = 0; cgb_mode < 2; ++cgb_mode) {
        gbb_instance *m = make_machine(cgb_mode);
        REQUIRE(m != NULL);
        REQUIRE(vram1_is_zero(m));
        memset(m->vram[1], 0xAA, GBB_VRAM_BANK_SIZE);
        REQUIRE(!vram1_is_zero(m));
        REQUIRE(gbb_reset(m) == GBB_OK);
        REQUIRE(vram1_is_zero(m));
        memset(m->vram[1], 0x55, GBB_VRAM_BANK_SIZE);
        gbb_instance *fresh = make_machine(cgb_mode); /* a new load into a new instance */
        REQUIRE(fresh != NULL && vram1_is_zero(fresh));
        gbb_destroy(fresh);
        gbb_destroy(m);
    }
    return 0;
}


/* ---- CGB-mode rendering (Phase 11 plan 11-03; D-01 to D-09) ---------------------------------------
 * State is written straight into VRAM, OAM and CRAM after load and reset, then three frames run so
 * rgb_completed holds a frame drawn entirely from that state. Expected colours come from the
 * decisions: the CRAM pattern makes every (palette, index) pair a distinct word. */
static const char *g_fixtures_root = NULL;

static gbb_instance *make_render(void) {
    gbb_instance *m = make_machine(1);
    if (m == NULL || gbb_reset(m) != GBB_OK) { gbb_destroy(m); return NULL; }
    for (unsigned p = 0; p < 8u; ++p)
        for (unsigned i = 0; i < 4u; ++i) {
            const unsigned at = p * 8u + i * 2u;
            const uint16_t bg = (uint16_t)(0x0100u | (p << 4) | i);
            const uint16_t obj = (uint16_t)(0x0200u | (p << 4) | i);
            m->bg_cram[at] = (uint8_t)bg; m->bg_cram[at + 1u] = (uint8_t)(bg >> 8);
            m->obj_cram[at] = (uint8_t)obj; m->obj_cram[at + 1u] = (uint8_t)(obj >> 8);
        }
    m->lcdc = 0x91u;
    return m;
}

static uint16_t bgcol(unsigned p, unsigned i) { return (uint16_t)(0x0100u | (p << 4) | i); }
static uint16_t objcol(unsigned p, unsigned i) { return (uint16_t)(0x0200u | (p << 4) | i); }

/* One tile row at 0x8000 addressing (tile * 16 + row * 2) in the given VRAM bank. */
static void tile_row(gbb_instance *m, unsigned bank, unsigned tile, unsigned row,
                     uint8_t low, uint8_t high) {
    m->vram[bank][tile * 16u + row * 2u] = low;
    m->vram[bank][tile * 16u + row * 2u + 1u] = high;
}

static void tile_solid(gbb_instance *m, unsigned bank, unsigned tile, unsigned index) {
    for (unsigned r = 0; r < 8u; ++r)
        tile_row(m, bank, tile, r, (index & 1u) ? 0xFFu : 0u, (index & 2u) ? 0xFFu : 0u);
}

static void map_fill(gbb_instance *m, unsigned bank, uint16_t base, uint8_t value) {
    memset(&m->vram[bank][base], value, 1024u);
}

static int render(gbb_instance *m) {
    for (unsigned f = 0; f < 3u; ++f) {
        gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_HALTED_IDLE) return 0;
    }
    return 1;
}

static uint16_t px(const gbb_instance *m, unsigned x, unsigned y) {
    return m->rgb_completed[y * GBB_FRAME_WIDTH + x];
}

static int all_zero8(const uint8_t *p, size_t n) {
    for (size_t i = 0; i < n; ++i) if (p[i] != 0u) return 0;
    return 1;
}
static int all_zero16(const uint16_t *p, size_t n) {
    for (size_t i = 0; i < n; ++i) if (p[i] != 0u) return 0;
    return 1;
}

/* Tile 1 solid index 2 across the whole 9800 map with the given attribute. */
static void solid_bg_scene(gbb_instance *m, uint8_t attr) {
    tile_solid(m, 0, 1, 2);
    map_fill(m, 0, 0x1800u, 1u);
    map_fill(m, 1, 0x1800u, attr);
}

static int cgb_rgb_store_bg_palette(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 5u);
    m->bg_cram[5u * 8u + 2u * 2u] = 0x34u;
    m->bg_cram[5u * 8u + 2u * 2u + 1u] = 0x12u;
    REQUIRE(render(m));
    for (unsigned i = 0; i < GBB_FRAME_PIXELS; ++i) REQUIRE(m->rgb_completed[i] == 0x1234u);
    gbb_destroy(m);
    return 0;
}

/* ---- Compat rendering (Phase 11 plan 11-04; D-17, D-18, D-39) ------------------------------------
 * The compat palette is written by the test itself: cpal(set, shade) is a distinct word per cell,
 * so an expected value is never read back from a core resolve. */
static uint16_t cpal(unsigned set, unsigned shade) { return (uint16_t)(0x0300u | (set << 4) | shade); }

static void compat_palette_write(gbb_instance *m) {
    for (unsigned set = 0; set < 3u; ++set)
        for (unsigned shade = 0; shade < 4u; ++shade) m->compat_rgb555[set][shade] = cpal(set, shade);
}

/* Compat machine: $143 = $00 on the CGB profile, BG index 0 mapped to shade 3 by BGP = $1B. */
static gbb_instance *make_compat(void) {
    gbb_instance *m = make_machine(0);
    if (m == NULL || gbb_reset(m) != GBB_OK) { gbb_destroy(m); return NULL; }
    compat_palette_write(m);
    m->lcdc = 0x91u;
    m->bgp = 0x1Bu;
    m->obp0 = 0xE4u;
    m->obp1 = 0xE4u;
    return m;
}

static void compat_obj(gbb_instance *m, unsigned slot, uint8_t y, uint8_t x, uint8_t tile, uint8_t attr) {
    m->oam[slot * 4u] = y; m->oam[slot * 4u + 1u] = x;
    m->oam[slot * 4u + 2u] = tile; m->oam[slot * 4u + 3u] = attr;
}

static void fill_valid_rom(uint8_t *rom, size_t size) {
    memset(rom, 0, size);
    rom[0x101] = 0xC3u; rom[0x102] = 0x50u; rom[0x103] = 0x01u;
    rom[0x150] = 0x18u; rom[0x151] = 0xFEu;
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

static int is_default_palette(const gbb_instance *m) {
    static const uint16_t ramp[4] = {0x639Fu, 0x4275u, 0x254Bu, 0x0421u};
    for (unsigned set = 0; set < 3u; ++set)
        for (unsigned shade = 0; shade < 4u; ++shade)
            if (m->compat_rgb555[set][shade] != ramp[shade]) return 0;
    return 1;
}

static int cgb_compat_internal_default(void) {
    static uint8_t rom[0x8000];
    fill_valid_rom(rom, sizeof(rom));
    for (int profile = 0; profile < 2; ++profile) {
        gbb_instance *m = NULL;
        REQUIRE(gbb_create(profile ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
        REQUIRE(is_default_palette(m));
        REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
        REQUIRE(is_default_palette(m));
        m->compat_rgb555[1][2] = 0x1111u; /* a host change must survive reset and reload */
        REQUIRE(gbb_reset(m) == GBB_OK);
        REQUIRE(m->compat_rgb555[1][2] == 0x1111u);
        REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
        REQUIRE(m->compat_rgb555[1][2] == 0x1111u);
        m->compat_rgb555[1][2] = 0x254Bu;
        REQUIRE(is_default_palette(m));
        gbb_destroy(m);
    }
    return 0;
}

static int cgb_compat_internal_bg(void) {
    gbb_instance *m = make_compat();
    REQUIRE(m != NULL);
    REQUIRE(render(m)); /* VRAM is zero: BG index 0, mapped to shade 3 by BGP = $1B */
    for (unsigned i = 0; i < GBB_FRAME_PIXELS; ++i) REQUIRE(m->rgb_completed[i] == cpal(0, 3));
    gbb_destroy(m);
    return 0;
}

static int cgb_compat_internal_obj_sets(void) {
    for (unsigned variant = 0; variant < 2u; ++variant) {
        gbb_instance *m = make_compat();
        REQUIRE(m != NULL);
        m->obp0 = 0x1Bu; /* index 1 -> shade 2 */
        m->obp1 = 0xE4u; /* index 1 -> shade 1 */
        tile_solid(m, 0, 2, 1);
        const uint8_t low = variant ? 0x0Fu : 0x00u; /* OAM bits 0-3 must have no effect */
        compat_obj(m, 0, 16u, 40u, 2u, (uint8_t)(0x00u | low));
        compat_obj(m, 1, 16u, 80u, 2u, (uint8_t)(0x10u | low));
        m->lcdc = 0x93u;
        REQUIRE(render(m));
        REQUIRE(px(m, 32, 0) == cpal(1, 2));
        REQUIRE(px(m, 72, 0) == cpal(2, 1));
        REQUIRE(px(m, 10, 0) == cpal(0, 3));
        gbb_destroy(m);
    }
    return 0;
}

static void compat_attr_scene(gbb_instance *m) {
    tile_solid(m, 0, 1, 2);
    map_fill(m, 0, 0x1800u, 1u);
    tile_solid(m, 0, 2, 1);
    compat_obj(m, 0, 16u, 40u, 2u, 0x00u);
    m->bgp = 0xE4u;
    m->lcdc = 0x93u;
}

static int cgb_compat_internal_attr_ignored(void) {
    gbb_instance *a = make_compat();
    gbb_instance *b = make_compat();
    REQUIRE(a != NULL && b != NULL);
    compat_attr_scene(a);
    compat_attr_scene(b);
    memset(b->vram[1], 0xFFu, GBB_VRAM_BANK_SIZE); /* palette 7, flips, bank, priority everywhere */
    b->oam[3] |= 0x0Fu;                           /* OAM bank bit 3 and palette bits 0-2 */
    b->vram_bank = 1u;
    b->opri = 1u;
    REQUIRE(render(a) && render(b));
    REQUIRE(px(a, 0, 20) == cpal(0, 2));
    REQUIRE(px(a, 32, 0) == cpal(1, 1));
    REQUIRE(memcmp(a->rgb_completed, b->rgb_completed, sizeof(a->rgb_completed)) == 0);
    gbb_destroy(a);
    gbb_destroy(b);
    return 0;
}

static int cgb_compat_internal_lcdc0(void) {
    gbb_instance *m = make_compat();
    REQUIRE(m != NULL);
    tile_solid(m, 0, 1, 3);
    map_fill(m, 0, 0x1800u, 1u);
    tile_solid(m, 0, 2, 1);
    compat_obj(m, 0, 16u, 40u, 2u, 0x80u); /* bit 7 priority: BG is index 0 so the object shows */
    m->bgp = 0xE4u;
    m->lcdc = 0x92u; /* display and OBJ on, BG off */
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 20) == cpal(0, 0)); /* BG index 0 through BGP, not the tile's index 3 */
    REQUIRE(px(m, 32, 0) == cpal(1, 1));
    gbb_destroy(m);
    return 0;
}

static int cgb_compat_internal_x_order(void) {
    for (unsigned equal_x = 0; equal_x < 2u; ++equal_x) {
        gbb_instance *m = make_compat();
        REQUIRE(m != NULL);
        tile_solid(m, 0, 2, 1); /* object A: OBP0 -> set 1, shade 1 */
        tile_solid(m, 0, 3, 2); /* object B: OBP1 -> set 2, shade 2 */
        compat_obj(m, 0, 16u, equal_x ? 40u : 44u, 2u, 0x00u);
        compat_obj(m, 1, 16u, 40u, 3u, 0x10u);
        m->lcdc = 0x93u;
        REQUIRE(render(m));
        if (equal_x) {
            REQUIRE(px(m, 35, 0) == cpal(1, 1)); /* equal X: lower OAM index wins */
        } else {
            REQUIRE(px(m, 37, 0) == cpal(2, 2)); /* smaller X (index 1) wins over index 0 */
            REQUIRE(px(m, 33, 0) == cpal(2, 2));
            REQUIRE(px(m, 41, 0) == cpal(1, 1));
        }
        gbb_destroy(m);
    }
    return 0;
}

static int cgb_compat_internal_live_config(void) {
    gbb_instance *m = make_compat();
    REQUIRE(m != NULL);
    m->bgp = 0xE4u;
    tile_solid(m, 0, 1, 2);
    map_fill(m, 0, 0x1800u, 1u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == cpal(0, 2) && px(m, 0, 140) == cpal(0, 2));
    /* Run to the next frame completion, then into the following frame down to about line 70. */
    const uint64_t generation = m->frame_generation;
    while (m->frame_generation == generation) gbb_run(m, 912u, NULL, 0);
    for (unsigned line = 0; line < 80u; ++line) gbb_run(m, 912u, NULL, 0); /* vblank plus ~70 lines */
    m->compat_rgb555[0][2] = 0x7001u; /* mid-frame palette change */
    for (unsigned i = 0; i < GBB_FRAME_PIXELS; ++i) REQUIRE(m->rgb_completed[i] == cpal(0, 2));
    const uint64_t next = m->frame_generation;
    while (m->frame_generation == next) gbb_run(m, 912u, NULL, 0);
    REQUIRE(px(m, 0, 10) == cpal(0, 2));  /* drawn before the change */
    REQUIRE(px(m, 0, 140) == 0x7001u);    /* drawn after the change */
    gbb_destroy(m);
    return 0;
}

static int cgb_rgb_store_shade_untouched(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 5u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == bgcol(5, 2));
    REQUIRE(all_zero8(m->frame_working, sizeof(m->frame_working)));
    REQUIRE(all_zero8(m->frame_completed, sizeof(m->frame_completed)));
    gbb_destroy(m);
    /* Compat mode ($143 = $00) also renders into the RGB store only (D-01, D-02). */
    m = make_compat();
    REQUIRE(m != NULL);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == cpal(0, 3));
    REQUIRE(all_zero8(m->frame_working, sizeof(m->frame_working)));
    REQUIRE(all_zero8(m->frame_completed, sizeof(m->frame_completed)));
    gbb_destroy(m);
    return 0;
}

static int cgb_rgb_store_dmg_untouched(void) {
    char path[1024];
    REQUIRE(g_fixtures_root != NULL);
    snprintf(path, sizeof(path), "%s/visible-demo/demo.gb", g_fixtures_root);
    size_t size = 0;
    uint8_t *rom = read_file(path, &size);
    REQUIRE(rom != NULL);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
    REQUIRE(render(m));
    REQUIRE(!all_zero8(m->frame_completed, sizeof(m->frame_completed)));
    REQUIRE(all_zero16(m->rgb_working, GBB_FRAME_PIXELS));
    REQUIRE(all_zero16(m->rgb_completed, GBB_FRAME_PIXELS));
    gbb_destroy(m);
    free(rom);
    return 0;
}

static int cgb_rgb_store_lcd_off(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 5u);
    REQUIRE(render(m));
    uint16_t before[GBB_FRAME_PIXELS];
    memcpy(before, m->rgb_completed, sizeof(before));
    REQUIRE(before[0] == bgcol(5, 2));
    write8(m, 0xFF40u, 0x11u);
    for (unsigned i = 0; i < GBB_FRAME_PIXELS; ++i) REQUIRE(m->rgb_working[i] == 0x7FFFu);
    REQUIRE(memcmp(before, m->rgb_completed, sizeof(before)) == 0);
    gbb_destroy(m);
    return 0;
}

static int cgb_rgb_store_reset(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 5u);
    REQUIRE(render(m));
    REQUIRE(m->frame_generation != 0u && !all_zero16(m->rgb_completed, GBB_FRAME_PIXELS));
    REQUIRE(gbb_reset(m) == GBB_OK);
    REQUIRE(all_zero16(m->rgb_working, GBB_FRAME_PIXELS));
    REQUIRE(all_zero16(m->rgb_completed, GBB_FRAME_PIXELS));
    REQUIRE(m->frame_generation == 0u);
    gbb_destroy(m);
    return 0;
}

static int cgb_rgb_store_bit15_masked(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 5u);
    m->bg_cram[5u * 8u + 2u * 2u] = 0xFFu;
    m->bg_cram[5u * 8u + 2u * 2u + 1u] = 0xFFu;
    REQUIRE(render(m));
    for (unsigned i = 0; i < GBB_FRAME_PIXELS; ++i) {
        REQUIRE(m->rgb_completed[i] <= 0x7FFFu);
        REQUIRE(m->rgb_completed[i] == 0x7FFFu);
    }
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_palette(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 3u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == bgcol(3, 2));
    REQUIRE(px(m, 159, 143) == bgcol(3, 2));
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_bank(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    tile_solid(m, 0, 1, 1);
    tile_solid(m, 1, 1, 3);
    map_fill(m, 0, 0x1800u, 1u);
    m->vram[1][0x1800u] = 0x08u; /* entry 0 reads tile data from bank 1; entry 1 from bank 0 */
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == bgcol(0, 3));
    REQUIRE(px(m, 8, 0) == bgcol(0, 1));
    gbb_destroy(m);
    return 0;
}

/* Tile 1: index 1 in column 0 only. Tile 2: index 1 in row 0 column 0 only. Map entries 0 and 1
 * use tile 1 without and with X flip; entries 2 and 3 use tile 2 without and with Y flip. */
static void flip_scene(gbb_instance *m, uint8_t extra) {
    for (unsigned r = 0; r < 8u; ++r) tile_row(m, 0, 1, r, 0x80u, 0u);
    tile_row(m, 0, 2, 0, 0x80u, 0u);
    m->vram[0][0x1800u + 0u] = 1u; m->vram[1][0x1800u + 0u] = extra;
    m->vram[0][0x1800u + 1u] = 1u; m->vram[1][0x1800u + 1u] = (uint8_t)(0x20u | extra);
    m->vram[0][0x1800u + 2u] = 2u; m->vram[1][0x1800u + 2u] = extra;
    m->vram[0][0x1800u + 3u] = 2u; m->vram[1][0x1800u + 3u] = (uint8_t)(0x40u | extra);
}

static int cgb_attr_xflip(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    flip_scene(m, 0u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 3) == bgcol(0, 1) && px(m, 7, 3) == bgcol(0, 0));
    REQUIRE(px(m, 8, 3) == bgcol(0, 0) && px(m, 15, 3) == bgcol(0, 1));
    /* Bit 5 changes columns only: the Y flipped entry keeps its pixel at column 0, not 7. */
    REQUIRE(px(m, 24, 7) == bgcol(0, 1) && px(m, 31, 7) == bgcol(0, 0));
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_yflip(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    flip_scene(m, 0u);
    REQUIRE(render(m));
    REQUIRE(px(m, 16, 0) == bgcol(0, 1) && px(m, 16, 7) == bgcol(0, 0));
    REQUIRE(px(m, 24, 0) == bgcol(0, 0) && px(m, 24, 7) == bgcol(0, 1));
    /* Bit 6 changes rows only: X flip alone leaves tile 1 rows identical top to bottom. */
    REQUIRE(px(m, 15, 0) == px(m, 15, 7));
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_bit4_ignored(void) {
    gbb_instance *a = make_render();
    gbb_instance *b = make_render();
    REQUIRE(a != NULL && b != NULL);
    flip_scene(a, 0x02u);
    flip_scene(b, 0x12u);
    REQUIRE(render(a) && render(b));
    REQUIRE(px(a, 0, 0) == bgcol(2, 1));
    REQUIRE(memcmp(a->rgb_completed, b->rgb_completed, sizeof(a->rgb_completed)) == 0);
    gbb_destroy(a);
    gbb_destroy(b);
    return 0;
}

/* Object 0 covers x 0-7 of lines 0-7 with tile 3 (solid index 1) and the given OAM attribute. */
static void priority_scene(gbb_instance *m, uint8_t bg_attr, uint8_t lcdc) {
    tile_solid(m, 0, 1, 1);
    tile_solid(m, 0, 3, 1);
    map_fill(m, 0, 0x1800u, 1u);
    map_fill(m, 1, 0x1800u, bg_attr);
    m->oam[0] = 16u; m->oam[1] = 8u; m->oam[2] = 3u; m->oam[3] = 0u;
    m->lcdc = lcdc;
}

static int cgb_attr_bg_priority(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    priority_scene(m, 0x80u, 0x93u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == bgcol(0, 1)); /* BG attribute 7 with LCDC.0 = 1 hides the object */
    REQUIRE(px(m, 9, 0) == bgcol(0, 1));
    gbb_destroy(m);
    m = make_render();
    REQUIRE(m != NULL);
    priority_scene(m, 0x80u, 0x92u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == objcol(0, 1)); /* LCDC.0 = 0 removes the priority */
    gbb_destroy(m);
    m = make_render();
    REQUIRE(m != NULL);
    priority_scene(m, 0x00u, 0x93u);
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == objcol(0, 1)); /* neither priority bit: the object wins */
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_lcdc0_bg_drawn(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    solid_bg_scene(m, 4u);
    m->lcdc = 0x90u;
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == bgcol(4, 2));
    REQUIRE(px(m, 80, 70) == bgcol(4, 2));
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_window_same_fetch(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    /* Window map 9C00 entry 0 only; tile 1 index 1 lives in bank 1: column 0 on row 0 and
     * column 7 on row 1. Attribute: palette 4, bank 1, X flip. */
    tile_row(m, 1, 1, 0, 0x80u, 0u);
    tile_row(m, 1, 1, 1, 0x01u, 0u);
    m->vram[0][0x1C00u] = 1u;
    m->vram[1][0x1C00u] = (uint8_t)(0x04u | 0x08u | 0x20u);
    m->wx = 7u; m->wy = 0u;
    m->lcdc = 0xF1u;
    REQUIRE(render(m));
    REQUIRE(px(m, 7, 0) == bgcol(4, 1) && px(m, 0, 0) == bgcol(4, 0));
    REQUIRE(px(m, 0, 1) == bgcol(4, 1) && px(m, 7, 1) == bgcol(4, 0));
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_window_lcdc0_clear(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    tile_solid(m, 0, 1, 2);
    map_fill(m, 0, 0x1C00u, 1u);
    m->wx = 7u; m->wy = 0u;
    m->lcdc = 0xF0u; /* window on, window map 9C00, BG bit 0 clear */
    REQUIRE(render(m));
    REQUIRE(px(m, 0, 0) == bgcol(0, 2));
    REQUIRE(px(m, 159, 143) == bgcol(0, 2));
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_obj_bank_palette(void) {
    uint16_t seen[4] = {0};
    const uint8_t attrs[4] = {0x0Bu, 0x1Bu, 0x03u, 0x13u};
    for (unsigned k = 0; k < 4u; ++k) {
        gbb_instance *m = make_render();
        REQUIRE(m != NULL);
        tile_solid(m, 0, 2, 1);
        tile_solid(m, 1, 2, 3);
        m->oam[0] = 16u; m->oam[1] = 8u; m->oam[2] = 2u; m->oam[3] = attrs[k];
        m->lcdc = 0x93u;
        REQUIRE(render(m));
        seen[k] = px(m, 0, 0);
        gbb_destroy(m);
    }
    REQUIRE(seen[0] == objcol(3, 3) && seen[1] == objcol(3, 3)); /* bank 1, bit 4 ignored */
    REQUIRE(seen[2] == objcol(3, 1) && seen[3] == objcol(3, 1)); /* bank 0 */
    return 0;
}

static void order_scene(gbb_instance *m) {
    tile_solid(m, 0, 2, 1);
    for (unsigned r = 0; r < 8u; ++r) tile_row(m, 0, 3, r, 0x80u, 0u);
    m->oam[0] = 16u; m->oam[1] = 12u; m->oam[2] = 2u; m->oam[3] = 1u;  /* index 0: x 4-11, palette 1 */
    m->oam[4] = 16u; m->oam[5] = 8u;  m->oam[6] = 2u; m->oam[7] = 2u;  /* index 1: x 0-7, palette 2 */
    m->lcdc = 0x93u;
}

static int cgb_attr_obj_oam_order(void) {
    gbb_instance *m = make_render();
    REQUIRE(m != NULL);
    order_scene(m);
    REQUIRE(render(m));
    REQUIRE(px(m, 2, 0) == objcol(2, 1));
    REQUIRE(px(m, 5, 0) == objcol(1, 1)); /* lower OAM index wins although its X is greater */
    gbb_destroy(m);
    m = make_render();
    REQUIRE(m != NULL);
    order_scene(m);
    m->oam[2] = 3u; /* index 0 is opaque only in its first column (x = 4) */
    REQUIRE(render(m));
    REQUIRE(px(m, 4, 0) == objcol(1, 1));
    REQUIRE(px(m, 5, 0) == objcol(2, 1)); /* the transparent winner pixel lets index 1 show */
    gbb_destroy(m);
    return 0;
}

static int cgb_attr_vbk_not_read(void) {
    gbb_instance *a = make_render();
    gbb_instance *b = make_render();
    REQUIRE(a != NULL && b != NULL);
    flip_scene(a, 0x01u);
    flip_scene(b, 0x01u);
    for (unsigned k = 0; k < 2u; ++k) {
        gbb_instance *m = k == 0u ? a : b;
        tile_solid(m, 0, 2, 1);
        tile_solid(m, 1, 2, 3);
        m->oam[0] = 16u; m->oam[1] = 40u; m->oam[2] = 2u; m->oam[3] = 0x0Au;
        m->lcdc = 0x93u;
    }
    b->vram_bank = 1u;
    b->opri = 1u;
    REQUIRE(render(a) && render(b));
    REQUIRE(px(a, 32, 0) == objcol(2, 3));
    REQUIRE(memcmp(a->rgb_completed, b->rgb_completed, sizeof(a->rgb_completed)) == 0);
    gbb_destroy(a);
    gbb_destroy(b);
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
    {"palette_cram_obj_autoinc", palette_cram_obj_autoinc},
    {"palette_cram_compat_ports", palette_cram_compat_ports},
    {"palette_opri_cgb", palette_opri_cgb},
    {"palette_opri_compat", palette_opri_compat},
    {"cgb_postboot_cram_white", cgb_postboot_cram_white},
    {"cgb_postboot_vram1_zero", cgb_postboot_vram1_zero},
    {"cgb_rgb_store_bg_palette", cgb_rgb_store_bg_palette},
    {"cgb_rgb_store_shade_untouched", cgb_rgb_store_shade_untouched},
    {"cgb_rgb_store_dmg_untouched", cgb_rgb_store_dmg_untouched},
    {"cgb_rgb_store_lcd_off", cgb_rgb_store_lcd_off},
    {"cgb_rgb_store_reset", cgb_rgb_store_reset},
    {"cgb_rgb_store_bit15_masked", cgb_rgb_store_bit15_masked},
    {"cgb_attr_palette", cgb_attr_palette},
    {"cgb_attr_bank", cgb_attr_bank},
    {"cgb_attr_xflip", cgb_attr_xflip},
    {"cgb_attr_yflip", cgb_attr_yflip},
    {"cgb_attr_bit4_ignored", cgb_attr_bit4_ignored},
    {"cgb_attr_bg_priority", cgb_attr_bg_priority},
    {"cgb_attr_lcdc0_bg_drawn", cgb_attr_lcdc0_bg_drawn},
    {"cgb_attr_window_same_fetch", cgb_attr_window_same_fetch},
    {"cgb_attr_window_lcdc0_clear", cgb_attr_window_lcdc0_clear},
    {"cgb_attr_obj_bank_palette", cgb_attr_obj_bank_palette},
    {"cgb_attr_obj_oam_order", cgb_attr_obj_oam_order},
    {"cgb_attr_vbk_not_read", cgb_attr_vbk_not_read},
    {"cgb_compat_internal_default", cgb_compat_internal_default},
    {"cgb_compat_internal_bg", cgb_compat_internal_bg},
    {"cgb_compat_internal_obj_sets", cgb_compat_internal_obj_sets},
    {"cgb_compat_internal_attr_ignored", cgb_compat_internal_attr_ignored},
    {"cgb_compat_internal_lcdc0", cgb_compat_internal_lcdc0},
    {"cgb_compat_internal_x_order", cgb_compat_internal_x_order},
    {"cgb_compat_internal_live_config", cgb_compat_internal_live_config},
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
    if (argc >= 3) g_fixtures_root = argv[2];
    for (size_t i = 0; i < sizeof(PLAIN_CASES) / sizeof(PLAIN_CASES[0]); ++i) {
        if (strcmp(argv[1], PLAIN_CASES[i].name) != 0) continue;
        int rc = PLAIN_CASES[i].run();
        if (rc == 0) printf("cgb-colour-internal %s pass\n", PLAIN_CASES[i].name);
        return rc;
    }
    return 2;
}
