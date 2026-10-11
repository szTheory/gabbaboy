#include "gbb_accept.h"

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

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "acceptance_digest_vectors_helper") == 0) return helper(argv[2]);
    fprintf(stderr, "usage: test_acceptance_digest acceptance_digest_vectors_helper <ppm-path>\n");
    return 2;
}
