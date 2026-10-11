#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* MagenTests mbc_oob_sram is hardware-derived (author-attested) evidence and is
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

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: test_magentests <case> <rom>...\n");
        return 2;
    }
    if (strcmp(argv[1], "magentests_oob_sram_mbc1") == 0 ||
        strcmp(argv[1], "magentests_oob_sram_mbc3") == 0 ||
        strcmp(argv[1], "magentests_oob_sram_mbc5") == 0)
        return oob_sram(argv[1], argv[2]);
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
