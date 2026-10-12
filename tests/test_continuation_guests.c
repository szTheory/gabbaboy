#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Core-level continuation of the original MBC3+timer, MBC2 and MBC5 guests (D-24 core half).
 *
 * Each guest has a store branch (fresh RAM) and a resume branch (marker intact). The test runs
 * the store branch in one instance, exports the battery image, imports it into a fresh instance,
 * optionally applies gbb_rtc_catch_up, runs the resume branch and reads the guest's WRAM
 * results. This is software continuation evidence; the player envelope and wrong-ROM identity
 * rejection are proved separately (Plan 09-16). Public API only; argv is <case> <rom>. */

#define SLICE UINT64_C(1048576)
#define MAX_SLICES 64u
#define SECONDS_PER_DAY 86400u

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

typedef struct {
    uint8_t *bytes;
    size_t size;
} image;

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

typedef struct {
    uint8_t published; /* C000: 1 after the store branch, 2 after the resume branch */
    uint8_t c[7];      /* C000..C006 */
} result;

static gbb_instance *fresh(const uint8_t *rom, size_t size) {
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK) return NULL;
    if (gbb_load_rom(m, rom, size) != GBB_OK) { gbb_destroy(m); return NULL; }
    return m;
}

/* Runs until the guest halts idle (it publishes C000 then HALTs), within 64 slices. */
static int run_to_idle(gbb_instance *m, result *out) {
    for (unsigned i = 0u; i < MAX_SLICES; ++i) {
        const gbb_run_result r = gbb_run(m, SLICE, NULL, 0u);
        if (r.reason == GBB_STOP_HALTED_IDLE) {
            for (unsigned a = 0u; a < 7u; ++a) out->c[a] = gbb_peek_ram(m, (uint16_t)(0xC000u + a));
            out->published = out->c[0];
            return 0;
        }
        if (r.reason != GBB_STOP_BUDGET) {
            fprintf(stderr, "unexpected stop reason %d\n", (int)r.reason);
            return 1;
        }
    }
    fprintf(stderr, "guest did not halt within %u slices\n", MAX_SLICES);
    return 1;
}

static int has_battery(const gbb_instance *m, size_t *battery) {
    return gbb_battery_size(m, battery) == GBB_OK && *battery > 0u;
}

/* Store run: fresh instance, optional seed image, run, export. */
static int store_run(const uint8_t *rom, size_t size, const image *seed, result *out, image *exported) {
    gbb_instance *m = fresh(rom, size);
    REQUIRE(m != NULL);
    if (seed != NULL) REQUIRE(gbb_import_battery(m, seed->bytes, seed->size) == GBB_OK);
    REQUIRE(run_to_idle(m, out) == 0);
    size_t n = 0u;
    REQUIRE(has_battery(m, &n));
    exported->bytes = malloc(n);
    REQUIRE(exported->bytes != NULL);
    exported->size = n;
    REQUIRE(gbb_copy_battery(m, exported->bytes, n) == GBB_OK);
    gbb_destroy(m);
    return 0;
}

/* Resume run: a different fresh instance imports the image, optionally catches up, runs. */
static int resume_run(const uint8_t *rom, size_t size, const image *img, int64_t catch_up_seconds,
                      result *out) {
    gbb_instance *m = fresh(rom, size);
    REQUIRE(m != NULL);
    REQUIRE(gbb_import_battery(m, img->bytes, img->size) == GBB_OK);
    if (catch_up_seconds > 0) REQUIRE(gbb_rtc_catch_up(m, catch_up_seconds) == GBB_OK);
    REQUIRE(run_to_idle(m, out) == 0);
    gbb_destroy(m);
    return 0;
}

/* Seed image for the MBC3 guest: a fresh instance's exported battery (RAM $FF plus a fresh RTC
 * block) with the mode byte at $A010 (RAM offset 0x10) set. */
static int make_seed(const uint8_t *rom, size_t size, uint8_t mode, image *seed) {
    gbb_instance *m = fresh(rom, size);
    REQUIRE(m != NULL);
    size_t n = 0u;
    REQUIRE(has_battery(m, &n));
    seed->bytes = malloc(n);
    REQUIRE(seed->bytes != NULL);
    seed->size = n;
    REQUIRE(gbb_copy_battery(m, seed->bytes, n) == GBB_OK);
    gbb_destroy(m);
    seed->bytes[0x10u] = mode;
    return 0;
}

static uint64_t total_seconds(const result *r) {
    /* C001..C005 = S, M, H, DL, DH */
    const uint64_t days = ((uint64_t)(r->c[5] & 1u) << 8) | r->c[4];
    return days * SECONDS_PER_DAY + (uint64_t)r->c[3] * 3600u + (uint64_t)r->c[2] * 60u + r->c[1];
}

static int mbc3_rtc(const uint8_t *rom, size_t size) {
    static const int64_t steps[] = { 0, 1, 59, 3600, 86400 };
    image img = { NULL, 0u };
    result stored;
    REQUIRE(store_run(rom, size, NULL, &stored, &img) == 0);
    REQUIRE(stored.published == 1u);
    uint64_t base = 0u;
    for (size_t i = 0u; i < sizeof(steps) / sizeof(steps[0]); ++i) {
        result r;
        REQUIRE(resume_run(rom, size, &img, steps[i], &r) == 0);
        REQUIRE(r.published == 2u);
        REQUIRE(r.c[6] == 0xA5u);
        if (i == 0u) base = total_seconds(&r);
        const uint64_t modulus = UINT64_C(512) * SECONDS_PER_DAY;
        const uint64_t delta = (total_seconds(&r) + modulus - base) % modulus;
        if (delta != (uint64_t)steps[i]) {
            fprintf(stderr, "N=%lld: result(N) - result(0) = %llu\n", (long long)steps[i],
                    (unsigned long long)delta);
            return 1;
        }
    }
    /* Adjacency edge (CART-06): the core has no ROM identity, so an image exported from this
     * guest is accepted by an instance running a different ROM of the same battery size (title
     * byte changed, header checksum fixed). Identity rejection lives in the player envelope. */
    uint8_t *other = malloc(size);
    REQUIRE(other != NULL);
    memcpy(other, rom, size);
    other[0x134u] ^= 0x01u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - other[i] - 1u);
    other[0x14Du] = checksum;
    result r;
    REQUIRE(resume_run(other, size, &img, 0, &r) == 0);
    REQUIRE(r.published == 2u);
    free(other);
    free(img.bytes);
    return 0;
}

static int mbc3_rtc_halted(const uint8_t *rom, size_t size) {
    image seed = { NULL, 0u }, img = { NULL, 0u };
    REQUIRE(make_seed(rom, size, 0x01u, &seed) == 0);
    result stored;
    REQUIRE(store_run(rom, size, &seed, &stored, &img) == 0);
    REQUIRE(stored.published == 1u);
    static const int64_t steps[] = { 0, 86400 };
    for (size_t i = 0u; i < 2u; ++i) {
        result r;
        REQUIRE(resume_run(rom, size, &img, steps[i], &r) == 0);
        REQUIRE(r.published == 2u);
        REQUIRE(r.c[1] == 56u && r.c[2] == 34u && r.c[3] == 12u && r.c[4] == 0u);
        REQUIRE((r.c[5] & 0x40u) != 0u);
        REQUIRE((r.c[5] & 0x81u) == 0u);
    }
    free(seed.bytes);
    free(img.bytes);
    return 0;
}

static int mbc3_rtc_carry(const uint8_t *rom, size_t size) {
    image seed = { NULL, 0u }, img = { NULL, 0u };
    REQUIRE(make_seed(rom, size, 0x02u, &seed) == 0);
    result stored;
    REQUIRE(store_run(rom, size, &seed, &stored, &img) == 0);
    REQUIRE(stored.published == 1u);
    result r;
    REQUIRE(resume_run(rom, size, &img, 0, &r) == 0);
    REQUIRE(r.published == 2u);
    REQUIRE((r.c[5] & 0x80u) == 0u);   /* no carry yet */
    REQUIRE((r.c[5] & 0x01u) == 1u && r.c[4] == 0xFFu); /* day 511 */
    REQUIRE(resume_run(rom, size, &img, 20, &r) == 0);
    REQUIRE(r.published == 2u);
    REQUIRE((r.c[5] & 0x80u) != 0u);   /* crossed day 511 */
    REQUIRE((r.c[5] & 0x01u) == 0u && r.c[4] == 0u); /* day 0 */
    free(seed.bytes);
    free(img.bytes);
    return 0;
}

/* MBC2 / MBC5: no timer, so no catch-up. The marker resumes from the imported image, and a
 * damaged image must not resume (the control that makes the pass meaningful). */
static int marker_guest(const uint8_t *rom, size_t size, size_t damage_offset) {
    image img = { NULL, 0u };
    result stored;
    REQUIRE(store_run(rom, size, NULL, &stored, &img) == 0);
    REQUIRE(stored.published == 1u);
    REQUIRE(damage_offset < img.size);
    result r;
    REQUIRE(resume_run(rom, size, &img, 0, &r) == 0);
    REQUIRE(r.published == 2u);
    REQUIRE(r.c[1] == 0xA5u);

    img.bytes[damage_offset] ^= 0x01u;
    REQUIRE(resume_run(rom, size, &img, 0, &r) == 0);
    REQUIRE(r.c[1] != 0xA5u);
    free(img.bytes);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: test_continuation_guests <case> <rom>\n");
        return 2;
    }
    size_t size = 0u;
    uint8_t *rom = read_file(argv[2], &size);
    if (rom == NULL) { fprintf(stderr, "cannot read %s\n", argv[2]); return 2; }
    int rc = 2;
    if (strcmp(argv[1], "continuation_guest_mbc3_rtc") == 0) rc = mbc3_rtc(rom, size);
    else if (strcmp(argv[1], "continuation_guest_mbc3_rtc_halted") == 0) rc = mbc3_rtc_halted(rom, size);
    else if (strcmp(argv[1], "continuation_guest_mbc3_rtc_carry") == 0) rc = mbc3_rtc_carry(rom, size);
    else if (strcmp(argv[1], "continuation_guest_mbc2") == 0) rc = marker_guest(rom, size, 300u);
    else if (strcmp(argv[1], "continuation_guest_mbc5") == 0) rc = marker_guest(rom, size, 15u * 8192u);
    else fprintf(stderr, "unknown case %s\n", argv[1]);
    free(rom);
    return rc;
}
