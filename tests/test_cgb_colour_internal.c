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
    return 2;
}
