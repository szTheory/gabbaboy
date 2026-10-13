#include "gabbaboy/gabbaboy.h"
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
    /* The pass path writes BGP = 0, so every BG pixel is shade 0: the default BG shade 0 value. */
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

int main(int argc, char **argv) {
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
    if (strcmp(argv[1], "magentests_cgb_ppu_disabled_state") == 0)
        return cgb_ppu_disabled_state(argv[1], argv[2]);
    if (strcmp(argv[1], "magentests_cgb_ppu_disabled_state_compat") == 0)
        return cgb_ppu_disabled_state_compat(argv[1], argv[2]);
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
