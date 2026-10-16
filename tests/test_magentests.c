#ifdef GBB_P13_CORE_SOURCE
#include GBB_P13_CORE_SOURCE
#else
#include "gabbaboy/gabbaboy.h"
#endif
#include "gbb_accept.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Phase 11 (D-21) adds CGB PPU ROMs, checked on GBB_PROFILE_CGB_CPU_E through
 * gbb_copy_frame_rgb555 against literal RGB555 structural predicates; see the CGB section below.
 *
 * MagenTests mbc_oob_sram is hardware-derived (author-attested) evidence and is
 * screen-only: the guest compares an out-of-bounds SRAM bank against bank 0 and
 * paints the whole screen white (shade 0) on a pass. Frames 1-3 are white
 * whatever the result, so the frame budget is deliberately well past 10 and a
 * paired negative control (header RAM code 0x03) must paint shade 3 instead.
 * Public API only: argv is the case name followed by ROM paths. */

#define WIDTH 160u
#define HEIGHT 144u
#define PIXELS 23040u /* 160 x 144 */
#define FRAME_HALF_DOTS 140448u
#define FRAMES 16u

static uint8_t *read_file(const char *path, size_t *out_size) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    const long n = ftell(f);
    if (n <= 0 || n > (1L << 22) || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    uint8_t *buf = malloc((size_t)n);
    if (buf != NULL && fread(buf, 1u, (size_t)n, f) != (size_t)n) { free(buf); buf = NULL; }
    fclose(f);
    *out_size = (size_t)n;
    return buf;
}

/* Runs FRAMES frames of half-dots in slices and requires every pixel to be `shade`. */
static int expect_screen(const char *label, const uint8_t *rom, size_t size, uint8_t shade) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return 1;
    if (gbb_load_rom(machine, rom, size) != GBB_OK) {
        fprintf(stderr, "%s: gbb_load_rom rejected the image\n", label);
        gbb_destroy(machine);
        return 1;
    }
    for (uint32_t frame = 0u; frame < FRAMES; ++frame) {
        const gbb_run_result run = gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u);
        if (run.reason != GBB_STOP_BUDGET && run.reason != GBB_STOP_HALTED_IDLE) {
            fprintf(stderr, "%s: unexpected stop reason %d at frame %u\n", label,
                    (int)run.reason, (unsigned)frame);
            gbb_destroy(machine);
            return 1;
        }
    }
    uint8_t pixels[PIXELS];
    gbb_frame_info info;
    const gbb_error copied = gbb_copy_frame(machine, pixels, sizeof(pixels), WIDTH, &info);
    gbb_destroy(machine);
    if (copied != GBB_OK || info.width != WIDTH || info.height != HEIGHT) {
        fprintf(stderr, "%s: gbb_copy_frame failed (%d)\n", label, (int)copied);
        return 1;
    }
    size_t histogram[4] = {0u, 0u, 0u, 0u};
    for (size_t i = 0u; i < PIXELS; ++i)
        if (pixels[i] < 4u) ++histogram[pixels[i]];
    if (histogram[shade] != PIXELS) {
        fprintf(stderr, "%s: after %u frames expected all %u pixels at shade %u; "
                "histogram 0:%zu 1:%zu 2:%zu 3:%zu\n", label, (unsigned)FRAMES,
                (unsigned)PIXELS, (unsigned)shade,
                histogram[0], histogram[1], histogram[2], histogram[3]);
        return 1;
    }
    return 0;
}

static int oob_sram(const char *label, const char *path) {
    size_t size = 0u;
    uint8_t *rom = read_file(path, &size);
    if (rom == NULL) { fprintf(stderr, "%s: cannot read %s\n", label, path); return 1; }
    const int rc = expect_screen(label, rom, size, 0u);
    free(rom);
    return rc;
}

/* Negative control: every ROM with its header RAM code forced to 0x03 (32 KiB, which
 * the guest does not expect) must paint shade 3, so a blank, early or constant
 * frame cannot satisfy both the pass cases and this control. */
static int negative_control(int count, char **paths) {
    for (int i = 0; i < count; ++i) {
        size_t size = 0u;
        uint8_t *rom = read_file(paths[i], &size);
        if (rom == NULL || size < 0x150u) {
            fprintf(stderr, "negative control: cannot read %s\n", paths[i]);
            free(rom);
            return 1;
        }
        rom[0x149u] = 0x03u;
        uint8_t checksum = 0u;
        for (size_t j = 0x134u; j <= 0x14Cu; ++j) checksum = (uint8_t)(checksum - rom[j] - 1u);
        rom[0x14Du] = checksum;
        const int rc = expect_screen(paths[i], rom, size, 3u);
        free(rom);
        if (rc != 0) return rc;
    }
    return 0;
}

/* ---- CGB PPU ROMs (Phase 11, D-21) ----
 * Each ROM runs a fixed 20 frames on the CGB profile. The last two completed frames must be
 * byte-identical and come from distinct LCD-on completions (generation advances), then a literal
 * RGB555 predicate typed from the pinned upstream source must hold, and only then is the frame
 * digest compared. The digest never decides pass or fail on its own. */
#define CGB_FRAMES 20u
#define PITCH_BYTES 320u
#define GREEN555 0x03E0u
#define RED555 0x001Fu
#define BLUE555 0x7C00u
#define WHITE555 0x7FFFu

static int cgb_capture(const char *label, const uint8_t *rom, size_t size, uint16_t *out,
                       uint16_t *previous) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK) return 1;
    if (gbb_load_rom(machine, rom, size) != GBB_OK) {
        fprintf(stderr, "%s: gbb_load_rom rejected the image\n", label);
        gbb_destroy(machine);
        return 1;
    }
    gbb_frame_info info_prev, info_last;
    memset(&info_prev, 0, sizeof(info_prev));
    memset(&info_last, 0, sizeof(info_last));
    for (uint32_t frame = 0u; frame < CGB_FRAMES; ++frame) {
        const gbb_run_result run = gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u);
        if (run.reason != GBB_STOP_BUDGET && run.reason != GBB_STOP_HALTED_IDLE) {
            fprintf(stderr, "%s: unexpected stop reason %d at frame %u\n", label,
                    (int)run.reason, (unsigned)frame);
            gbb_destroy(machine);
            return 1;
        }
        if (frame == CGB_FRAMES - 2u) {
            if (gbb_copy_frame_rgb555(machine, previous, PITCH_BYTES * HEIGHT, PITCH_BYTES,
                                      &info_prev) != GBB_OK) {
                fprintf(stderr, "%s: gbb_copy_frame_rgb555 failed\n", label);
                gbb_destroy(machine);
                return 1;
            }
        }
    }
    const gbb_error copied = gbb_copy_frame_rgb555(machine, out, PITCH_BYTES * HEIGHT,
                                                   PITCH_BYTES, &info_last);
    gbb_destroy(machine);
    if (copied != GBB_OK || info_last.width != WIDTH || info_last.height != HEIGHT) {
        fprintf(stderr, "%s: gbb_copy_frame_rgb555 failed (%d)\n", label, (int)copied);
        return 1;
    }
    if (info_last.generation <= info_prev.generation) {
        fprintf(stderr, "%s: generation did not advance between the last two captures "
                "(%llu then %llu): a retained frame is not an LCD-on completion\n", label,
                (unsigned long long)info_prev.generation,
                (unsigned long long)info_last.generation);
        return 1;
    }
    if (memcmp(previous, out, PIXELS * sizeof(uint16_t)) != 0) {
        fprintf(stderr, "%s: the last two completed frames differ\n", label);
        return 1;
    }
    return 0;
}

static int cgb_expect_pixel(const char *label, const uint16_t *frame, unsigned x, unsigned y,
                            unsigned expected) {
    const unsigned got = frame[y * WIDTH + x];
    if (got == expected) return 0;
    fprintf(stderr, "%s: pixel %u,%u expected 0x%04X got 0x%04X\n", label, x, y, expected, got);
    return 1;
}

static int cgb_expect_digest(const char *label, const uint16_t *frame, const char *expected) {
    char hex[65];
    if (gbb_accept_rgb555_digest(frame, PITCH_BYTES, hex) != 0) {
        fprintf(stderr, "%s: frame is not valid RGB555\n", label);
        return 1;
    }
    if (strcmp(hex, expected) != 0) {
        fprintf(stderr, "%s: observed digest %s expected %s\n", label, hex, expected);
        return 1;
    }
    return 0;
}

static int cgb_load(const char *label, const char *path, uint8_t **rom, size_t *size) {
    *rom = read_file(path, size);
    if (*rom == NULL) { fprintf(stderr, "%s: cannot read %s\n", label, path); return 1; }
    return 0;
}

/* ppu_disabled_state: the guest turns the LCD off at vblank, reads STAT and expects mode 0;
 * it paints BG colour 1 green on a pass and red on a fail. All 23040 pixels must be green. An
 * LCD-off white frame (0x7FFF) or the failure red both miss. */
#define PPU_DISABLED_DIGEST "7a137aaa9e15d61c56d78c0c02b507099f29b1ab7bff6cadd5df6980c0c510e0"
static int cgb_ppu_disabled_state(const char *label, const char *path) {
    static uint16_t last[PIXELS], previous[PIXELS];
    uint8_t *rom; size_t size;
    if (cgb_load(label, path, &rom, &size) != 0) return 1;
    int rc = cgb_capture(label, rom, size, last, previous);
    free(rom);
    if (rc != 0) return 1;
    for (unsigned y = 0u; y < HEIGHT; ++y)
        for (unsigned x = 0u; x < WIDTH; ++x)
            if (cgb_expect_pixel(label, last, x, y, GREEN555) != 0) return 1;
    return cgb_expect_digest(label, last, PPU_DISABLED_DIGEST);
}

/* The same ROM with $143 cleared runs in compatibility mode, where the guest's CRAM writes are
 * ignored: the result must be one uniform default BG value, not the CGB green. */
static int cgb_ppu_disabled_state_compat(const char *label, const char *path) {
    static uint16_t last[PIXELS], previous[PIXELS];
    uint8_t *rom; size_t size;
    if (cgb_load(label, path, &rom, &size) != 0) return 1;
    rom[0x143u] = 0x00u;
    uint8_t checksum = 0u;
    for (size_t j = 0x134u; j <= 0x14Cu; ++j) checksum = (uint8_t)(checksum - rom[j] - 1u);
    rom[0x14Du] = checksum;
    int rc = cgb_capture(label, rom, size, last, previous);
    free(rom);
    if (rc != 0) return 1;
    /* The guest paints colour index 1 across the screen. Its pass path writes BGP = 0x00 (index 1
     * -> shade 0) and its fail path BGP = 0x0C (index 1 -> shade 3), so the verdict stays visible
     * in compat mode as bg[0] versus bg[3]. The lcd_off_no_mode0_compat mutant proves it. */
    gbb_instance *probe = NULL;
    gbb_compat_palette palette;
    memset(&palette, 0, sizeof(palette));
    palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &probe) != GBB_OK ||
        gbb_get_compat_palette(probe, &palette) != GBB_OK) {
        gbb_destroy(probe);
        return 1;
    }
    gbb_destroy(probe);
    if (palette.bg[0] == GREEN555) { fprintf(stderr, "%s: default BG shade 0 collides with green\n", label); return 1; }
    for (unsigned y = 0u; y < HEIGHT; ++y)
        for (unsigned x = 0u; x < WIDTH; ++x)
            if (cgb_expect_pixel(label, last, x, y, palette.bg[0]) != 0) return 1;
    return 0;
}

/* oam_internal_priority: four triangle objects (two per box) drawn from tile rows 1-6, opaque
 * columns 1-6. Mask derived from the pinned source (see ELIGIBILITY.md "oam_internal_priority
 * mask derivation"): G is object colour 1 (green), R is object colour 2 (red), . is the white
 * BG. Each 12x6 box spans x 33-44; the green triangle comes from the object at X=40 (x 32-39)
 * and the red one from X=46 (x 38-45). The two never share an opaque pixel, so this ROM does
 * not constrain object ordering; the truth table does. */
#define BOX_X 33u
#define BOX_W 12u
#define BOX_H 6u
static const char *const oam_box_rows[BOX_H] = {
    ".....G.....R",
    "....GG....RR",
    "...GGG...RRR",
    "..GGGG..RRRR",
    ".GGGGG.RRRRR",
    "GGGGGGRRRRRR",
};
static const unsigned oam_box_y[2] = {25u, 45u};
#define OAM_INTERNAL_DIGEST "edf38b0b758a27d2d5c0fee8e0664b51e66dfbd380dfb23f950d6a145ae06299"
static int cgb_oam_internal_priority(const char *label, const char *path) {
    static uint16_t last[PIXELS], previous[PIXELS];
    uint8_t *rom; size_t size;
    if (cgb_load(label, path, &rom, &size) != 0) return 1;
    int rc = cgb_capture(label, rom, size, last, previous);
    free(rom);
    if (rc != 0) return 1;
    unsigned opaque = 0u;
    for (unsigned y = 0u; y < HEIGHT; ++y) {
        for (unsigned x = 0u; x < WIDTH; ++x) {
            unsigned expected = WHITE555;
            for (unsigned box = 0u; box < 2u; ++box) {
                if (y >= oam_box_y[box] && y < oam_box_y[box] + BOX_H &&
                    x >= BOX_X && x < BOX_X + BOX_W) {
                    const char c = oam_box_rows[y - oam_box_y[box]][x - BOX_X];
                    if (c == 'G') { expected = GREEN555; ++opaque; }
                    else if (c == 'R') { expected = RED555; ++opaque; }
                }
            }
            if (cgb_expect_pixel(label, last, x, y, expected) != 0) return 1;
        }
    }
    if (opaque != 84u) { fprintf(stderr, "%s: mask has %u opaque pixels, expected 84\n", label, opaque); return 1; }
    return cgb_expect_digest(label, last, OAM_INTERNAL_DIGEST);
}

/* bg_oam_priority: eight 8x8 cells at x 32-39, y 16k to 16k+7. Objects 1, 4, 5, 6, 7 draw an
 * all-colour-1 tile and win on every band (green). Objects 0, 2, 3 draw a half-green half-red tile
 * and the BG (blue) wins on the colour-1 rows because OAM bit 7, BG attribute bit 7 and LCDC.0 are
 * all set where required. No pixel is ever the failure red 0x001F. */
#define BG_OAM_DIGEST "5a356fe01e4eddb98ac204bd963bf5249d0a685d69b5a404eaa897ef476b895a"
static int cgb_bg_oam_priority(const char *label, const char *path) {
    static uint16_t last[PIXELS], previous[PIXELS];
    uint8_t *rom; size_t size;
    if (cgb_load(label, path, &rom, &size) != 0) return 1;
    int rc = cgb_capture(label, rom, size, last, previous);
    free(rom);
    if (rc != 0) return 1;
    for (unsigned y = 0u; y < HEIGHT; ++y) {
        for (unsigned x = 0u; x < WIDTH; ++x) {
            unsigned expected = WHITE555;
            if (x >= 32u && x < 40u && y < 128u) {
                const unsigned cell = y / 16u;
                const unsigned row = y % 16u;
                if (row < 8u) {
                    const int split = cell == 0u || cell == 2u || cell == 3u;
                    expected = (split && row >= 4u) ? BLUE555 : GREEN555;
                }
            }
            if (cgb_expect_pixel(label, last, x, y, expected) != 0) return 1;
        }
    }
    return cgb_expect_digest(label, last, BG_OAM_DIGEST);
}

#ifdef GBB_P13_CORE_SOURCE
/* Phase 13 CGB HDMA source-derived Magen oracle. This target includes the private
 * core TU only to verify guest VRAM/FF55/HALT state and exercise the bounded P13-05
 * runtime masks; display capture and digest still use the public API. */
extern void gbb_p12_set_mutants(uint64_t mask);
enum {
    MAGEN_HDMA_FRAMES = 20u,
    MAGEN_HDMA_OBSERVER_CAPACITY = 8192u,
    MAGEN_HDMA_MAP_OFFSET = 0x1800u,
    MAGEN_HDMA_MAP_BYTES = 0x400u,
    MAGEN_HDMA_BLOCKS = 64u
};
#define MAGEN_HDMA_NO_COPY_MASK (UINT64_C(1) << 41)
#define MAGEN_HDMA_WRONG_BANK_MASK (UINT64_C(1) << 43)
#define MAGEN_HDMA_HALT_ADMISSION_MASK (UINT64_C(1) << 48)
#define MAGEN_HDMA_FRAME_DIGEST "7a137aaa9e15d61c56d78c0c02b507099f29b1ab7bff6cadd5df6980c0c510e0"

typedef enum {
    MAGEN_HDMA_PASS = 0,
    MAGEN_HDMA_RUN_FAILURE,
    MAGEN_HDMA_FRAME_FAILURE,
    MAGEN_HDMA_STATUS_FAILURE,
    MAGEN_HDMA_HALT_FAILURE,
    MAGEN_HDMA_NO_COPY_FAILURE,
    MAGEN_HDMA_WRONG_BANK_FAILURE,
    MAGEN_HDMA_SCREEN_FAILURE,
    MAGEN_HDMA_DIGEST_FAILURE
} magen_hdma_result;

typedef struct {
    int saw_busy_read;
    int saw_complete_read;
    int bank0_map_matches_source;
    int bank1_map_matches_source;
    int halted;
    int transfer_active;
    uint16_t bank0_tile1_bytes;
    uint16_t bank1_tile1_bytes;
    uint16_t bank0_mismatch_offsets[8];
    uint8_t bank0_mismatch_values[8];
    uint8_t bank0_mismatch_count;
    uint8_t mode;
    uint8_t pending_hblank;
    uint8_t control_readback;
    uint16_t blocks_remaining;
    uint64_t previous_generation;
    uint64_t last_generation;
} magen_hdma_observation;

static const char *magen_hdma_reason(magen_hdma_result result) {
    switch (result) {
    case MAGEN_HDMA_PASS: return "pass";
    case MAGEN_HDMA_RUN_FAILURE: return "magen-hdma-run-budget-or-stop";
    case MAGEN_HDMA_FRAME_FAILURE: return "magen-hdma-fresh-stable-frame";
    case MAGEN_HDMA_STATUS_FAILURE: return "magen-hdma-guest-ff55-status";
    case MAGEN_HDMA_HALT_FAILURE: return "magen-hdma-halt-blocks-second-transfer";
    case MAGEN_HDMA_NO_COPY_FAILURE: return "magen-hdma-first-transfer-copies-map";
    case MAGEN_HDMA_WRONG_BANK_FAILURE: return "magen-hdma-first-transfer-vram-bank";
    case MAGEN_HDMA_SCREEN_FAILURE: return "magen-hdma-source-derived-green-screen";
    case MAGEN_HDMA_DIGEST_FAILURE: return "magen-hdma-structural-frame-digest";
    }
    return "magen-hdma-unknown";
}

static magen_hdma_result magen_hdma_capture(const char *label, const uint8_t *rom, size_t size,
                                             uint64_t mutant_mask,
                                             magen_hdma_observation *observation,
                                             uint16_t *last, uint16_t *previous) {
    gbb_instance *machine = NULL;
    gbb_test_bus_event *events = NULL;
    gbb_frame_info info_previous, info_last;
    memset(observation, 0, sizeof(*observation));
    memset(&info_previous, 0, sizeof(info_previous));
    memset(&info_last, 0, sizeof(info_last));
    gbb_p12_set_mutants(mutant_mask);
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK) return MAGEN_HDMA_RUN_FAILURE;
    if (gbb_load_rom(machine, rom, size) != GBB_OK) {
        fprintf(stderr, "%s: gbb_load_rom rejected the image\n", label);
        gbb_destroy(machine);
        return MAGEN_HDMA_RUN_FAILURE;
    }
    events = calloc(MAGEN_HDMA_OBSERVER_CAPACITY, sizeof(*events));
    if (events == NULL) {
        fprintf(stderr, "%s: cannot allocate bounded FF55 observer\n", label);
        gbb_destroy(machine);
        return MAGEN_HDMA_RUN_FAILURE;
    }
    gbb_test_observer_set(machine, events, MAGEN_HDMA_OBSERVER_CAPACITY);
    for (uint32_t frame = 0u; frame < MAGEN_HDMA_FRAMES; ++frame) {
        const gbb_run_result run = gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u);
        if ((run.reason != GBB_STOP_BUDGET && run.reason != GBB_STOP_HALTED_IDLE) ||
            run.consumed_half_dots == 0u || run.consumed_half_dots > FRAME_HALF_DOTS) {
            fprintf(stderr, "%s: unexpected stop/budget reason=%d consumed=%llu frame=%u\n",
                    label, (int)run.reason, (unsigned long long)run.consumed_half_dots,
                    (unsigned)frame);
            free(events);
            gbb_destroy(machine);
            return MAGEN_HDMA_RUN_FAILURE;
        }
        if (frame == MAGEN_HDMA_FRAMES - 2u &&
            gbb_copy_frame_rgb555(machine, previous, PITCH_BYTES * HEIGHT, PITCH_BYTES,
                                  &info_previous) != GBB_OK) {
            fprintf(stderr, "%s: previous RGB555 frame copy failed\n", label);
            free(events);
            gbb_destroy(machine);
            return MAGEN_HDMA_FRAME_FAILURE;
        }
    }
    if (gbb_copy_frame_rgb555(machine, last, PITCH_BYTES * HEIGHT, PITCH_BYTES,
                              &info_last) != GBB_OK ||
        info_last.width != WIDTH || info_last.height != HEIGHT ||
        info_last.generation <= info_previous.generation ||
        memcmp(previous, last, PIXELS * sizeof(uint16_t)) != 0) {
        fprintf(stderr, "%s: final frames must be stable distinct LCD-on completions\n", label);
        free(events);
        gbb_destroy(machine);
        return MAGEN_HDMA_FRAME_FAILURE;
    }
    if (gbb_test_observer_count(machine) >= MAGEN_HDMA_OBSERVER_CAPACITY) {
        fprintf(stderr, "%s: bounded FF55 observer capacity was exhausted\n", label);
        free(events);
        gbb_destroy(machine);
        return MAGEN_HDMA_RUN_FAILURE;
    }
    for (size_t i = 0u; i < gbb_test_observer_count(machine); ++i) {
        if (events[i].access == 1u && events[i].address == 0xFF55u) {
            if ((events[i].value & 0x80u) == 0u) observation->saw_busy_read = 1;
            if (events[i].value == 0xFFu) observation->saw_complete_read = 1;
        }
    }
    for (unsigned i = 0u; i < MAGEN_HDMA_MAP_BYTES; ++i) {
        if (machine->vram[0][MAGEN_HDMA_MAP_OFFSET + i] == 1u)
            ++observation->bank0_tile1_bytes;
        else if (observation->bank0_mismatch_count < 8u) {
            const unsigned slot = observation->bank0_mismatch_count++;
            observation->bank0_mismatch_offsets[slot] = (uint16_t)i;
            observation->bank0_mismatch_values[slot] = machine->vram[0][MAGEN_HDMA_MAP_OFFSET + i];
        }
        if (machine->vram[1][MAGEN_HDMA_MAP_OFFSET + i] == 1u)
            ++observation->bank1_tile1_bytes;
    }
    observation->bank0_map_matches_source = 1;
    observation->bank1_map_matches_source = 1;
    for (unsigned i = 0u; i < MAGEN_HDMA_MAP_BYTES; ++i) {
        const uint8_t expected = i < 12u ? 0xFFu : 1u;
        if (machine->vram[0][MAGEN_HDMA_MAP_OFFSET + i] != expected)
            observation->bank0_map_matches_source = 0;
        if (machine->vram[1][MAGEN_HDMA_MAP_OFFSET + i] != expected)
            observation->bank1_map_matches_source = 0;
    }
    observation->halted = machine->halted;
    observation->transfer_active = machine->hdma.active;
    observation->mode = machine->hdma.mode;
    observation->pending_hblank = machine->hdma.pending_hblank;
    observation->control_readback = machine->hdma.control_readback;
    observation->blocks_remaining = machine->hdma.blocks_remaining;
    observation->previous_generation = info_previous.generation;
    observation->last_generation = info_last.generation;
    free(events);
    gbb_destroy(machine);
    return MAGEN_HDMA_PASS;
}

static magen_hdma_result magen_hdma_check(const char *label, const char *path,
                                           uint64_t mutant_mask, int compare_digest) {
    static uint16_t last[PIXELS], previous[PIXELS];
    magen_hdma_observation observation;
    uint8_t *rom = NULL;
    size_t size = 0u;
    magen_hdma_result result;
    if (cgb_load(label, path, &rom, &size) != 0) return MAGEN_HDMA_RUN_FAILURE;
    result = magen_hdma_capture(label, rom, size, mutant_mask, &observation, last, previous);
    free(rom);
    if (result != MAGEN_HDMA_PASS) return result;
    if (!observation.saw_busy_read || !observation.saw_complete_read) {
        fprintf(stderr, "%s: FF55 guest status must show busy then complete; busy=%d complete=%d\n",
                label, observation.saw_busy_read, observation.saw_complete_read);
        return MAGEN_HDMA_STATUS_FAILURE;
    }
    if (!observation.halted || observation.mode != 1u || observation.transfer_active != 0 ||
        observation.blocks_remaining != MAGEN_HDMA_BLOCKS ||
        observation.control_readback != 0x3Fu) {
        fprintf(stderr, "%s: HALT must block second HDMA at 64 blocks; halted=%d mode=%u active=%d pending=%u remaining=%u FF55=%02X\n",
                label, observation.halted, observation.mode, observation.transfer_active,
                observation.pending_hblank,
                (unsigned)observation.blocks_remaining, observation.control_readback);
        return MAGEN_HDMA_HALT_FAILURE;
    }
    if (!observation.bank0_map_matches_source) {
        if (observation.bank1_map_matches_source) {
            fprintf(stderr, "%s: first HDMA selected VRAM bank 1; tile-1 bytes bank0=%u bank1=%u\n",
                    label, (unsigned)observation.bank0_tile1_bytes,
                    (unsigned)observation.bank1_tile1_bytes);
            return MAGEN_HDMA_WRONG_BANK_FAILURE;
        }
        fprintf(stderr, "%s: first HDMA map data missing; tile-1 bytes bank0=%u bank1=%u\n",
                label, (unsigned)observation.bank0_tile1_bytes,
                (unsigned)observation.bank1_tile1_bytes);
        for (unsigned i = 0u; i < observation.bank0_mismatch_count; ++i)
            fprintf(stderr, "%s: map offset=$%03X actual=%02X\n", label,
                    observation.bank0_mismatch_offsets[i],
                    observation.bank0_mismatch_values[i]);
        return MAGEN_HDMA_NO_COPY_FAILURE;
    }
    for (size_t i = 0u; i < PIXELS; ++i) {
        if (last[i] != GREEN555) {
            fprintf(stderr, "%s: source-derived green screen expected 0x%04X at pixel %zu,%zu got 0x%04X\n",
                    label, GREEN555, i % WIDTH, i / WIDTH, last[i]);
            return MAGEN_HDMA_SCREEN_FAILURE;
        }
    }
    if (compare_digest) {
        char actual[65];
        if (gbb_accept_rgb555_digest(last, PITCH_BYTES, actual) != 0) {
            fprintf(stderr, "%s: structural frame is not valid RGB555\n", label);
            return MAGEN_HDMA_DIGEST_FAILURE;
        }
        if (strcmp(actual, MAGEN_HDMA_FRAME_DIGEST) != 0) {
            fprintf(stderr, "%s: structural frame digest %s expected %s\n", label, actual,
                    MAGEN_HDMA_FRAME_DIGEST);
            return MAGEN_HDMA_DIGEST_FAILURE;
        }
        printf("magen-hdma-structural-pass digest=%s generations=%llu,%llu\n", actual,
               (unsigned long long)observation.previous_generation,
               (unsigned long long)observation.last_generation);
    }
    return MAGEN_HDMA_PASS;
}

static int magen_hdma_controls(const char *path) {
    static const struct {
        const char *name;
        uint64_t mask;
        magen_hdma_result expected;
    } controls[] = {
        {"no-transfer", MAGEN_HDMA_NO_COPY_MASK, MAGEN_HDMA_NO_COPY_FAILURE},
        {"wrong-bank", MAGEN_HDMA_WRONG_BANK_MASK, MAGEN_HDMA_WRONG_BANK_FAILURE},
        {"wrong-HALT", MAGEN_HDMA_HALT_ADMISSION_MASK, MAGEN_HDMA_HALT_FAILURE}
    };
    for (size_t i = 0u; i < sizeof(controls) / sizeof(controls[0]); ++i) {
        magen_hdma_result result = magen_hdma_check(controls[i].name, path,
                                                     controls[i].mask, 0);
        if (result != controls[i].expected) {
            fprintf(stderr, "cgb-hdma-magen-control %s expected=%s actual=%s\n",
                    controls[i].name, magen_hdma_reason(controls[i].expected),
                    magen_hdma_reason(result));
            return 1;
        }
        printf("cgb-hdma-magen-control %s detected=%s\n", controls[i].name,
               magen_hdma_reason(result));
    }
    puts("cgb-hdma-magen-controls pass");
    return 0;
}
#endif /* GBB_P13_CORE_SOURCE */

static void report_cgb_success(const char *case_id, const char *mode,
                               const char *assertion_id) {
    printf("magentests guest-result case=%s model=CGB-CPU-E mode=%s speed=normal observed=pass evaluator_status=pass terminal=1 assertions=1 assertion_id=%s\n",
           case_id, mode, assertion_id);
}

int main(int argc, char **argv) {
#ifdef GBB_P13_CORE_SOURCE
    if (argc == 5 && strcmp(argv[3], "--mutants") == 0) {
        char *end = NULL;
        unsigned long long mask = strtoull(argv[4], &end, 0);
        if (end == argv[4] || *end != '\0') return 2;
        gbb_p12_set_mutants((uint64_t)mask);
        argc -= 2;
    }
#endif
    if (argc < 3) {
        fprintf(stderr, "usage: test_magentests <case> <rom>...\n");
        return 2;
    }
    if (strcmp(argv[1], "magentests_oob_sram_mbc1") == 0 ||
        strcmp(argv[1], "magentests_oob_sram_mbc3") == 0 ||
        strcmp(argv[1], "magentests_oob_sram_mbc5") == 0)
        return oob_sram(argv[1], argv[2]);
    if (strcmp(argv[1], "magentests_oob_sram_negative_control") == 0)
        return negative_control(argc - 2, argv + 2);
    if (strcmp(argv[1], "magentests_cgb_ppu_disabled_state") == 0) {
        const int result = cgb_ppu_disabled_state(argv[1], argv[2]);
        if (result == 0) report_cgb_success("ppu_disabled_state:native", "native",
                                             "lcd-off-stat-mode0-display");
        return result;
    }
    if (strcmp(argv[1], "magentests_cgb_ppu_disabled_state_compat") == 0) {
        const int result = cgb_ppu_disabled_state_compat(argv[1], argv[2]);
        if (result == 0) report_cgb_success("ppu_disabled_state:compat", "compat",
                                             "lcd-off-stat-mode0-display");
        return result;
    }
    if (strcmp(argv[1], "magentests_cgb_oam_internal_priority") == 0) {
        const int result = cgb_oam_internal_priority(argv[1], argv[2]);
        if (result == 0) report_cgb_success("oam_internal_priority", "native",
                                             "oam-internal-priority-source-frame");
        return result;
    }
    if (strcmp(argv[1], "magentests_cgb_bg_oam_priority") == 0) {
        const int result = cgb_bg_oam_priority(argv[1], argv[2]);
        if (result == 0) report_cgb_success("bg_oam_priority", "native",
                                             "bg-oam-priority-source-frame");
        return result;
    }
#ifdef GBB_P13_CORE_SOURCE
    if (strcmp(argv[1], "magentests_hblank_vram_dma") == 0) {
        const int result = magen_hdma_check(argv[1], argv[2], 0u, 1);
        if (result == 0) report_cgb_success("hblank_vram_dma", "native",
                                             "hblank-vram-dma-source-contract");
        return result;
    }
    if (strcmp(argv[1], "cgb_hdma_magen_controls") == 0)
        return magen_hdma_controls(argv[2]);
#endif
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
