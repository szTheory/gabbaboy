#include "gbb_accept.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Helper for the independent digest vector check (rgb-digest-vector.py --check). It builds the
 * same synthetic frame and PCM vector the python script builds and prints the C digests, so the
 * two implementations are compared byte for byte. The frame is stored with a pitch wider than the
 * row and an invalid shade in the padding, which proves padding is never read. */

#define PITCH (GBB_ACCEPT_FRAME_WIDTH + 4u)

static int helper(const char *ppm_path) {
    static uint8_t frame[PITCH * GBB_ACCEPT_FRAME_HEIGHT];
    memset(frame, 9, sizeof(frame)); /* padding is not a valid shade */
    for (size_t y = 0; y < GBB_ACCEPT_FRAME_HEIGHT; ++y) {
        for (size_t x = 0; x < GBB_ACCEPT_FRAME_WIDTH; ++x) frame[y * PITCH + x] = (uint8_t)((x + 2u * y) % 4u);
    }
    char rgb[65];
    if (gbb_accept_rgb_digest(frame, PITCH, rgb) != 0) return 1;
    if (gbb_accept_write_ppm(ppm_path, frame, PITCH) != 0) return 1;
    printf("rgb_sha256=%s\n", rgb);

    static const gbb_audio_frame pcm[] = {{-1, 258}, {32767, -32768}, {0, 1}};
    gbb_accept_pcm_digest_ctx ctx;
    char pcm_hex[65];
    gbb_accept_pcm_digest_init(&ctx);
    gbb_accept_pcm_digest_feed(&ctx, pcm, sizeof(pcm) / sizeof(pcm[0]));
    gbb_accept_pcm_digest_final(&ctx, pcm_hex);
    printf("pcm_sha256=%s\n", pcm_hex);

    /* A shade above 3 is an error and must not produce a digest or a file. */
    frame[5u * PITCH + 7u] = 4u;
    char bad[65] = "unchanged";
    char bad_path[1024];
    snprintf(bad_path, sizeof(bad_path), "%s.invalid", ppm_path);
    int rejected = gbb_accept_rgb_digest(frame, PITCH, bad) != 0 && strcmp(bad, "unchanged") == 0 &&
                   gbb_accept_write_ppm(bad_path, frame, PITCH) != 0;
    FILE *leftover = fopen(bad_path, "rb");
    if (leftover != NULL) {
        fclose(leftover);
        rejected = 0;
    }
    printf("invalid_shade=%s\n", rejected ? "rejected" : "accepted");
    return 0;
}

/* RGB555 helper (rgb-digest-vector.py --rgb555 --check). The synthetic frame is (x * 37 + y * 101) & 0x7FFF.
 * A second copy with a 400-byte pitch and 0xFFFF garbage past the 320-byte row proves padding is never read. */
#define PITCH555_BYTES 400u

static int helper555(const char *ppm_path) {
    static uint16_t frame[GBB_ACCEPT_FRAME_WIDTH * GBB_ACCEPT_FRAME_HEIGHT];
    static uint16_t padded[(PITCH555_BYTES / 2u) * GBB_ACCEPT_FRAME_HEIGHT];
    const size_t padded_stride = PITCH555_BYTES / 2u;
    memset(padded, 0xFF, sizeof(padded));
    for (size_t y = 0; y < GBB_ACCEPT_FRAME_HEIGHT; ++y) {
        for (size_t x = 0; x < GBB_ACCEPT_FRAME_WIDTH; ++x) {
            uint16_t v = (uint16_t)((x * 37u + y * 101u) & 0x7FFFu);
            frame[y * GBB_ACCEPT_FRAME_WIDTH + x] = v;
            padded[y * padded_stride + x] = v;
        }
    }
    char hex[65], hex_padded[65];
    if (gbb_accept_rgb555_digest(frame, GBB_ACCEPT_FRAME_WIDTH * 2u, hex) != 0) return 1;
    if (gbb_accept_rgb555_digest(padded, PITCH555_BYTES, hex_padded) != 0) return 1;
    printf("rgb555_sha256=%s\npadded_pitch_sha256=%s\n", hex, hex_padded);

    printf("expand5=");
    for (unsigned c = 0; c < 32u; ++c) {
        if (gbb_accept_expand5(c) != (uint8_t)((c << 3) | (c >> 2))) return 1;
        printf("%02x", gbb_accept_expand5(c));
    }
    printf("\n");

    int wrote = gbb_accept_write_ppm_rgb555(ppm_path, frame, GBB_ACCEPT_FRAME_WIDTH * 2u) == 0;
    printf("ppm=%s\n", wrote ? "written" : "failed");

    /* 0x8000 is invalid: no digest text, no file. */
    frame[5u * GBB_ACCEPT_FRAME_WIDTH + 7u] = 0x8000u;
    char bad[65] = "unchanged";
    char bad_path[1024];
    snprintf(bad_path, sizeof(bad_path), "%s.invalid", ppm_path);
    int rejected = gbb_accept_rgb555_digest(frame, GBB_ACCEPT_FRAME_WIDTH * 2u, bad) != 0 &&
                   strcmp(bad, "unchanged") == 0 &&
                   gbb_accept_write_ppm_rgb555(bad_path, frame, GBB_ACCEPT_FRAME_WIDTH * 2u) != 0;
    FILE *leftover = fopen(bad_path, "rb");
    if (leftover != NULL) {
        fclose(leftover);
        rejected = 0;
    }
    printf("invalid_value=%s\n", rejected ? "rejected" : "accepted");

    /* IN-03 hardening: a misaligned base, a NULL path and a NULL output are refused, not read.
     * Exit code only, so the printed vector set stays unchanged. */
    static uint8_t raw[GBB_ACCEPT_FRAME_WIDTH * GBB_ACCEPT_FRAME_HEIGHT * 2u + 2u];
    const uint16_t *aligned = (const uint16_t *)(void *)(raw + ((uintptr_t)raw & 1u));
    const uint16_t *odd = (const uint16_t *)(const void *)((const uint8_t *)aligned + 1);
    uint8_t bin[32];
    char odd_hex[65] = "unchanged";
    frame[5u * GBB_ACCEPT_FRAME_WIDTH + 7u] = 0u;
    if (gbb_accept_rgb555_digest_bin(frame, GBB_ACCEPT_FRAME_WIDTH * 2u, bin) != 0) return 1;
    if (gbb_accept_rgb555_digest(odd, GBB_ACCEPT_FRAME_WIDTH * 2u, odd_hex) == 0 ||
        strcmp(odd_hex, "unchanged") != 0) return 1;
    if (gbb_accept_rgb555_digest_bin(frame, GBB_ACCEPT_FRAME_WIDTH * 2u, NULL) == 0) return 1;
    if (gbb_accept_write_ppm_rgb555(NULL, frame, GBB_ACCEPT_FRAME_WIDTH * 2u) == 0) return 1;
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "acceptance_digest_rgb555_helper") == 0) return helper555(argv[2]);
    if (argc == 3 && strcmp(argv[1], "acceptance_digest_vectors_helper") == 0) return helper(argv[2]);
    fprintf(stderr, "usage: test_acceptance_digest acceptance_digest_vectors_helper <ppm-path>\n");
    return 2;
}
