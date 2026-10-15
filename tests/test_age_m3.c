/* Bounded AGE mode-3 source-image capture through the public guest API. */
#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"
#include "gabbaboy_test.h"

#include <inttypes.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define AGE_ROM_BYTES 32768u
#define FRAME_WIDTH 160u
#define FRAME_HEIGHT 144u
#define PIXEL_COUNT (FRAME_WIDTH * FRAME_HEIGHT)
#define FRAME_BYTES (PIXEL_COUNT * 2u)
#define FRAME_HALF_DOTS UINT64_C(140448)
/* Source setup clears 10,240 VRAM bytes before it enables LCD; reserve five
 * further VBlanks from the source counter plus a bounded setup margin. */
#define MAX_RUN_HALF_DOTS (FRAME_HALF_DOTS * UINT64_C(16))
#define RUN_SLICE UINT64_C(2048)
#define MAX_PATH_BYTES 1024u

typedef struct {
    const char *case_name;
    uint8_t header_143;
    gbb_exec_mode mode;
    uint8_t double_speed;
} age_m3_case;

static const age_m3_case age_m3_cases[] = {
    {"m3-bg-lcdc-cgbBCE", 0x80u, GBB_MODE_CGB, 0u},
    {"m3-bg-lcdc-nocgb-ncmBCE", 0x00u, GBB_MODE_CGB_DMG_COMPAT, 0u},
    {"m3-bg-lcdc-ds-cgbBCE", 0xC0u, GBB_MODE_CGB, 1u},
    {"m3-bg-scx-cgbBCE", 0x80u, GBB_MODE_CGB, 0u},
    {"m3-bg-scx-nocgb-ncmBCE", 0x00u, GBB_MODE_CGB_DMG_COMPAT, 0u},
    {"m3-bg-scx-ds-cgbBCE", 0xC0u, GBB_MODE_CGB, 1u},
};

static const uint16_t compat_palette_bg[4] = {0x639Fu, 0x4275u, 0x254Bu, 0x0421u};

static const age_m3_case *find_case(const char *name) {
    for (size_t i = 0u; i < sizeof(age_m3_cases) / sizeof(age_m3_cases[0]); ++i) {
        if (strcmp(name, age_m3_cases[i].case_name) == 0) return &age_m3_cases[i];
    }
    return NULL;
}

static int parse_u64(const char *text, uint64_t *out) {
    char *end = NULL;
    unsigned long long value;
    if (text == NULL || text[0] == '\0' || text[0] == '-') return 0;
    errno = 0;
    value = strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') return 0;
    *out = (uint64_t)value;
    return 1;
}

static int read_rom(const char *path, uint8_t rom[AGE_ROM_BYTES]) {
    FILE *file = fopen(path, "rb");
    size_t count;
    int extra;
    int failed;
    if (file == NULL) {
        fprintf(stderr, "age-m3 rom-open-failed\n");
        return 0;
    }
    count = fread(rom, 1u, AGE_ROM_BYTES, file);
    failed = ferror(file);
    extra = fgetc(file);
    fclose(file);
    if (failed || count != AGE_ROM_BYTES || extra != EOF) {
        fprintf(stderr, "age-m3 rom-size-invalid expected=%u\n", AGE_ROM_BYTES);
        return 0;
    }
    return 1;
}

static int compat_palette_is_policy(const gbb_instance *instance) {
    gbb_compat_palette palette;
    memset(&palette, 0, sizeof(palette));
    palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    if (gbb_get_compat_palette(instance, &palette) != GBB_OK ||
        palette.struct_size != GBB_COMPAT_PALETTE_SIZE_V1) {
        fprintf(stderr, "age-m3 compat-palette-read-failed\n");
        return 0;
    }
    for (size_t i = 0u; i < 4u; ++i) {
        if (palette.bg[i] != compat_palette_bg[i]) {
            fprintf(stderr, "age-m3 compat-palette-policy-mismatch shade=%zu\n", i);
            return 0;
        }
    }
    return 1;
}

static int write_file(const char *path, const uint8_t *bytes, size_t size) {
    FILE *file = fopen(path, "wb");
    int ok;
    int close_ok;
    if (file == NULL) {
        fprintf(stderr, "age-m3 output-open-failed\n");
        return 0;
    }
    ok = fwrite(bytes, 1u, size, file) == size;
    if (fflush(file) != 0) ok = 0;
    close_ok = fclose(file) == 0;
    if (!close_ok) ok = 0;
    if (!ok) {
        fprintf(stderr, "age-m3 output-write-failed\n");
        return 0;
    }
    return 1;
}

static int write_metadata(const char *frame_path, const age_m3_case *test_case,
                          const char *rom_sha256, const char *frame_sha256,
                          uint64_t generation, uint32_t width, uint32_t height) {
    char metadata_path[MAX_PATH_BYTES];
    char metadata[1024];
    const char *mode = test_case->mode == GBB_MODE_CGB ? "native-cgb" : "dmg-compatibility";
    const char *speed = test_case->double_speed ? "double" : "normal";
    int path_length = snprintf(metadata_path, sizeof(metadata_path), "%s.json", frame_path);
    int metadata_length;
    FILE *file;
    int ok;
    int close_ok;
    if (path_length < 0 || (size_t)path_length >= sizeof(metadata_path)) {
        fprintf(stderr, "age-m3 metadata-path-too-long\n");
        return 0;
    }
    metadata_length = snprintf(metadata, sizeof(metadata),
        "{\"schema\":\"gabbaboy-age-m3-frame-v1\",\"case\":\"%s\","
        "\"model\":\"CGB-E\",\"mode\":\"%s\",\"speed\":\"%s\","
        "\"terminal\":\"frame-counter-vblank-5\",\"generation\":%" PRIu64 ","
        "\"width\":%" PRIu32 ",\"height\":%" PRIu32 ","
        "\"rom_sha256\":\"%s\",\"frame_sha256\":\"%s\","
        "\"compat_palette_bg\":[%u,%u,%u,%u]}\n",
        test_case->case_name, mode, speed, generation, width, height, rom_sha256, frame_sha256,
        (unsigned)compat_palette_bg[0], (unsigned)compat_palette_bg[1],
        (unsigned)compat_palette_bg[2], (unsigned)compat_palette_bg[3]);
    if (metadata_length < 0 || (size_t)metadata_length >= sizeof(metadata)) {
        fprintf(stderr, "age-m3 metadata-size-invalid\n");
        return 0;
    }
    file = fopen(metadata_path, "wb");
    if (file == NULL) {
        fprintf(stderr, "age-m3 metadata-open-failed\n");
        return 0;
    }
    ok = fwrite(metadata, 1u, (size_t)metadata_length, file) == (size_t)metadata_length;
    if (fflush(file) != 0) ok = 0;
    close_ok = fclose(file) == 0;
    if (!close_ok) ok = 0;
    if (!ok) {
        fprintf(stderr, "age-m3 metadata-write-failed\n");
        return 0;
    }
    return 1;
}

static int run_case(const age_m3_case *test_case, const char *rom_path,
                    const char *frame_path, uint64_t max_run_half_dots) {
    uint8_t rom[AGE_ROM_BYTES];
    uint8_t frame_bytes[FRAME_BYTES];
    uint16_t pixels[PIXEL_COUNT];
    char rom_sha256[65];
    char frame_sha256[65];
    gbb_instance *instance = NULL;
    gbb_frame_info frame_info;
    gbb_info info;
    uint64_t elapsed = 0u;
    uint8_t double_speed = 0u;
    int have_frame = 0;
    gbb_error error;

    if (!read_rom(rom_path, rom)) return 1;
    if (rom[0x143u] != test_case->header_143) {
        fprintf(stderr, "age-m3 rom-mode-header-mismatch case=%s expected=%02x actual=%02x\n",
                test_case->case_name, test_case->header_143, rom[0x143u]);
        return 1;
    }
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &instance) != GBB_OK || instance == NULL) {
        fprintf(stderr, "age-m3 create-failed\n");
        gbb_destroy(instance);
        return 1;
    }
    error = gbb_load_rom(instance, rom, sizeof(rom));
    if (error != GBB_OK) {
        fprintf(stderr, "age-m3 load-rom-failed error=%d\n", (int)error);
        gbb_destroy(instance);
        return 1;
    }
    memset(&info, 0, sizeof(info));
    info.struct_size = GBB_INFO_SIZE_V1;
    if (gbb_get_info(instance, &info) != GBB_OK ||
        info.profile != GBB_PROFILE_CGB_CPU_E || info.mode != (uint32_t)test_case->mode ||
        info.cgb_flag != test_case->header_143) {
        fprintf(stderr, "age-m3 loaded-mode-mismatch case=%s\n", test_case->case_name);
        gbb_destroy(instance);
        return 1;
    }
    if (!compat_palette_is_policy(instance)) {
        gbb_destroy(instance);
        return 1;
    }

    while (elapsed < max_run_half_dots) {
        const uint64_t remaining = max_run_half_dots - elapsed;
        const uint64_t slice = remaining < RUN_SLICE ? remaining : RUN_SLICE;
        const gbb_run_result run = gbb_run(instance, slice, NULL, 0u);
        if (run.consumed_half_dots > remaining) {
            fprintf(stderr, "age-m3 run-exceeded-bound\n");
            gbb_destroy(instance);
            return 1;
        }
        elapsed += run.consumed_half_dots;
        if (run.reason != GBB_STOP_BUDGET) {
            fprintf(stderr, "age-m3 run-stopped reason=%d\n", (int)run.reason);
            gbb_destroy(instance);
            return 1;
        }
        error = gbb_copy_frame_rgb555(instance, pixels, sizeof(pixels),
                                      FRAME_WIDTH * sizeof(uint16_t), &frame_info);
        if (error == GBB_OK) {
            if (frame_info.width != FRAME_WIDTH || frame_info.height != FRAME_HEIGHT ||
                frame_info.generation > 5u) {
                fprintf(stderr, "age-m3 wrong-frame generation=%" PRIu64 "\n", frame_info.generation);
                gbb_destroy(instance);
                return 1;
            }
            /* The pinned AGE source turns LCD off during setup, seeds its
             * VBlank counter to five, then enables LCD. Generation 5 is the
             * first completed frame at the source's terminal boundary. */
            if (frame_info.generation == 5u) {
                have_frame = 1;
                break;
            }
        } else if (error != GBB_FRAME_NOT_READY) {
            fprintf(stderr, "age-m3 frame-copy-failed error=%d\n", (int)error);
            gbb_destroy(instance);
            return 1;
        }
        if (run.consumed_half_dots == 0u) {
            fprintf(stderr, "age-m3 run-made-no-progress\n");
            gbb_destroy(instance);
            return 1;
        }
    }
    if (!have_frame) {
        fprintf(stderr, "age-m3 source-frame-not-complete bound=%" PRIu64 "\n", max_run_half_dots);
        gbb_destroy(instance);
        return 1;
    }
    gbb_test_speed_state(instance, &double_speed, NULL, NULL, NULL);
    if (double_speed != test_case->double_speed) {
        fprintf(stderr, "age-m3 actual-speed-mismatch case=%s expected=%s actual=%s\n",
                test_case->case_name, test_case->double_speed ? "double" : "normal",
                double_speed ? "double" : "normal");
        gbb_destroy(instance);
        return 1;
    }
    for (size_t i = 0u; i < PIXEL_COUNT; ++i) {
        if (pixels[i] > 0x7FFFu) {
            fprintf(stderr, "age-m3 rgb555-out-of-range pixel=%zu\n", i);
            gbb_destroy(instance);
            return 1;
        }
        frame_bytes[i * 2u] = (uint8_t)(pixels[i] & 0xFFu);
        frame_bytes[i * 2u + 1u] = (uint8_t)(pixels[i] >> 8);
    }
    gbb_accept_sha256_hex(rom, sizeof(rom), rom_sha256);
    gbb_accept_sha256_hex(frame_bytes, sizeof(frame_bytes), frame_sha256);
    if (!write_file(frame_path, frame_bytes, sizeof(frame_bytes)) ||
        !write_metadata(frame_path, test_case, rom_sha256, frame_sha256,
                        frame_info.generation, frame_info.width, frame_info.height)) {
        gbb_destroy(instance);
        return 1;
    }
    printf("age-m3-frame pass case=%s model=CGB-E mode=%s speed=%s generation=%" PRIu64
           " elapsed_half_dots=%" PRIu64 " frame_sha256=%s\n",
           test_case->case_name,
           test_case->mode == GBB_MODE_CGB ? "native-cgb" : "dmg-compatibility",
           double_speed ? "double" : "normal", frame_info.generation, elapsed, frame_sha256);
    gbb_destroy(instance);
    return 0;
}

int main(int argc, char **argv) {
    const age_m3_case *test_case = NULL;
    const char *rom_path = NULL;
    const char *frame_path = NULL;
    uint64_t max_run_half_dots = MAX_RUN_HALF_DOTS;
    if ((argc != 7 && argc != 9) || strcmp(argv[1], "--case") != 0 ||
        strcmp(argv[3], "--rom") != 0 || strcmp(argv[5], "--frame") != 0) {
        fprintf(stderr, "usage: test_age_m3 --case CASE --rom ROM --frame RGB555 [--max-half-dots N]\n");
        return 2;
    }
    if (argc == 9 && (strcmp(argv[7], "--max-half-dots") != 0 ||
                      !parse_u64(argv[8], &max_run_half_dots) ||
                      max_run_half_dots == 0u || max_run_half_dots > MAX_RUN_HALF_DOTS)) {
        fprintf(stderr, "age-m3 run-bound-invalid\n");
        return 2;
    }
    test_case = find_case(argv[2]);
    rom_path = argv[4];
    frame_path = argv[6];
    if (test_case == NULL) {
        fprintf(stderr, "age-m3 unknown-case\n");
        return 2;
    }
    if (strlen(rom_path) >= MAX_PATH_BYTES || strlen(frame_path) >= MAX_PATH_BYTES) {
        fprintf(stderr, "age-m3 path-too-long\n");
        return 2;
    }
    return run_case(test_case, rom_path, frame_path, max_run_half_dots);
}
