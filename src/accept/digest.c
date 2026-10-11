#include "gbb_accept.h"

#include <stdio.h>
#include <string.h>

/* Canonical frame and PCM digests (D-16, D-24, D-33). Every hashed or written
 * byte is built explicitly here, so the result does not depend on host
 * endianness, struct layout or text-mode file translation. */

static const uint8_t SHADE_TO_GRAY[4] = {255u, 170u, 85u, 0u};

static int shades_valid(const uint8_t *shades, size_t pitch) {
    for (size_t y = 0; y < GBB_ACCEPT_FRAME_HEIGHT; ++y) {
        const uint8_t *row = shades + y * pitch;
        for (size_t x = 0; x < GBB_ACCEPT_FRAME_WIDTH; ++x) {
            if (row[x] > 3u) return 0;
        }
    }
    return 1;
}

static void expand_row(const uint8_t *row, uint8_t rgb[GBB_ACCEPT_FRAME_WIDTH * 3u]) {
    for (size_t x = 0; x < GBB_ACCEPT_FRAME_WIDTH; ++x) {
        uint8_t gray = SHADE_TO_GRAY[row[x]];
        rgb[x * 3u] = gray;
        rgb[x * 3u + 1u] = gray;
        rgb[x * 3u + 2u] = gray;
    }
}

int gbb_accept_rgb_digest(const uint8_t *shades, size_t pitch, char out_hex[65]) {
    if (!shades_valid(shades, pitch)) return 1;
    gbb_accept_sha256_ctx ctx;
    uint8_t rgb[GBB_ACCEPT_FRAME_WIDTH * 3u];
    gbb_accept_sha256_init(&ctx);
    gbb_accept_sha256_update(&ctx, (const uint8_t *)GBB_ACCEPT_RGB_HEADER,
                             sizeof(GBB_ACCEPT_RGB_HEADER) - 1u);
    for (size_t y = 0; y < GBB_ACCEPT_FRAME_HEIGHT; ++y) {
        expand_row(shades + y * pitch, rgb);
        gbb_accept_sha256_update(&ctx, rgb, sizeof(rgb));
    }
    gbb_accept_sha256_final(&ctx, out_hex);
    return 0;
}

static int hex_nibble(char c) {
    return c >= 'a' ? c - 'a' + 10 : c - '0';
}

int gbb_accept_rgb_digest_bin(const uint8_t *shades, size_t pitch, uint8_t out[32]) {
    char hex[65];
    if (gbb_accept_rgb_digest(shades, pitch, hex) != 0) return 1;
    for (size_t i = 0; i < 32u; ++i) {
        out[i] = (uint8_t)((hex_nibble(hex[i * 2u]) << 4) | hex_nibble(hex[i * 2u + 1u]));
    }
    return 0;
}

int gbb_accept_write_ppm(const char *path, const uint8_t *shades, size_t pitch) {
    static const char header[] = "P6\n160 144\n255\n";
    if (!shades_valid(shades, pitch)) return 1;
    FILE *file = fopen(path, "wb");
    if (file == NULL) return 2;
    int failed = fwrite(header, 1, sizeof(header) - 1u, file) != sizeof(header) - 1u;
    uint8_t rgb[GBB_ACCEPT_FRAME_WIDTH * 3u];
    for (size_t y = 0; y < GBB_ACCEPT_FRAME_HEIGHT && !failed; ++y) {
        expand_row(shades + y * pitch, rgb);
        failed = fwrite(rgb, 1, sizeof(rgb), file) != sizeof(rgb);
    }
    if (fclose(file) != 0) failed = 1;
    return failed ? 3 : 0;
}

unsigned gbb_accept_frame_distinct_shades(const uint8_t *shades, size_t pitch) {
    unsigned seen = 0;
    for (size_t y = 0; y < GBB_ACCEPT_FRAME_HEIGHT; ++y) {
        const uint8_t *row = shades + y * pitch;
        for (size_t x = 0; x < GBB_ACCEPT_FRAME_WIDTH; ++x) {
            if (row[x] > 3u) return 0;
            seen |= 1u << row[x];
        }
    }
    unsigned count = 0;
    for (unsigned shade = 0; shade < 4u; ++shade) count += (seen >> shade) & 1u;
    return count;
}

void gbb_accept_pcm_digest_init(gbb_accept_pcm_digest_ctx *ctx) {
    gbb_accept_sha256_init(&ctx->sha);
}

void gbb_accept_pcm_digest_feed(gbb_accept_pcm_digest_ctx *ctx, const gbb_audio_frame *frames,
                                size_t count) {
    uint8_t bytes[256u * 4u];
    while (count != 0) {
        size_t chunk = count < 256u ? count : 256u;
        for (size_t i = 0; i < chunk; ++i) {
            /* uint16_t conversion is modulo 2^16, so negative samples serialize as two's complement. */
            uint16_t left = (uint16_t)frames[i].left;
            uint16_t right = (uint16_t)frames[i].right;
            bytes[i * 4u] = (uint8_t)(left & 0xFFu);
            bytes[i * 4u + 1u] = (uint8_t)(left >> 8);
            bytes[i * 4u + 2u] = (uint8_t)(right & 0xFFu);
            bytes[i * 4u + 3u] = (uint8_t)(right >> 8);
        }
        gbb_accept_sha256_update(&ctx->sha, bytes, chunk * 4u);
        frames += chunk;
        count -= chunk;
    }
}

void gbb_accept_pcm_digest_final(gbb_accept_pcm_digest_ctx *ctx, char out_hex[65]) {
    gbb_accept_sha256_final(&ctx->sha, out_hex);
}

void gbb_accept_pcm_stats_init(gbb_accept_pcm_stats *stats) {
    memset(stats, 0, sizeof(*stats));
}

static void channel_feed(gbb_accept_pcm_channel_stats *channel, uint64_t index, int16_t sample) {
    if (index == 0) {
        channel->min = sample;
        channel->max = sample;
    } else {
        if (sample < channel->min) channel->min = sample;
        if (sample > channel->max) channel->max = sample;
        if (sample != channel->last) ++channel->changes;
    }
    channel->last = sample;
}

void gbb_accept_pcm_stats_feed(gbb_accept_pcm_stats *stats, const gbb_audio_frame *frames,
                               size_t count) {
    for (size_t i = 0; i < count; ++i) {
        channel_feed(&stats->left, stats->samples, frames[i].left);
        channel_feed(&stats->right, stats->samples, frames[i].right);
        ++stats->samples;
    }
}

int32_t gbb_accept_pcm_peak_to_peak(const gbb_accept_pcm_channel_stats *channel, uint64_t samples) {
    if (samples == 0) return 0;
    return (int32_t)channel->max - (int32_t)channel->min;
}

bool gbb_accept_pcm_audible(const gbb_accept_pcm_stats *stats) {
    return gbb_accept_pcm_peak_to_peak(&stats->left, stats->samples) >= GBB_ACCEPT_PCM_MIN_PEAK_TO_PEAK &&
           gbb_accept_pcm_peak_to_peak(&stats->right, stats->samples) >= GBB_ACCEPT_PCM_MIN_PEAK_TO_PEAK &&
           stats->left.changes >= GBB_ACCEPT_PCM_MIN_CHANGES &&
           stats->right.changes >= GBB_ACCEPT_PCM_MIN_CHANGES;
}
