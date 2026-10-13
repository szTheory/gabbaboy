/* White-box speed checks (Phase 12). The baseline identity case is intentionally
 * committed before the first Phase 12 core change. */
#ifdef GBB_P12_CORE_SOURCE
#include GBB_P12_CORE_SOURCE
#else
#include "../src/core/gabbaboy.c"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef GBB_P12_MUTANT_BUILD
#include <errno.h>
extern uint64_t gbb_p12_mutants;
#endif

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define FRAME_HALF_DOTS 140448u
#define FNV_OFFSET UINT64_C(0xCBF29CE484222325)
#define FNV_PRIME UINT64_C(0x100000001B3)

typedef struct { const char *path; uint64_t digest; } speed_pin;

/* Recorded at the pre-phase head fb45111 from the unmodified core. These are
 * regression identities, not hardware evidence. */
static const speed_pin SPEED_PINS[] = {
    {"cgb-colour/colour-attr.gb", UINT64_C(0x20c5f5bcd3de4db5)},
    {"cgb-colour/colour-compat.gb", UINT64_C(0xcfb2b0a18be42fb5)},
    {"cgb-colour/colour-cram.gb", UINT64_C(0x40aa92e3715d65b5)},
    {"cgb-colour/colour-hblank.gb", UINT64_C(0x7194fc1cb88beeb5)},
    {"cgb-colour/colour-lcdc0.gb", UINT64_C(0x16eb0caed53fcdb5)},
    {"cgb-colour/colour-lcdoff.gb", UINT64_C(0x5612e439ca9135b5)},
    {"cgb-banking/banking-cgb.gb", UINT64_C(0x9d5155c3b02fcb95)},
    {"<inline-timer-serial-dma>", UINT64_C(0xef296435e5cc0741)}
};

static void hash_bytes(uint64_t *hash, const void *data, size_t size) {
    const uint8_t *bytes = data;
    for (size_t i = 0; i < size; ++i) {
        *hash ^= bytes[i];
        *hash *= FNV_PRIME;
    }
}

static uint8_t *read_file(const char *path, size_t *size) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return NULL;
    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return NULL; }
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) { fclose(file); return NULL; }
    uint8_t *bytes = malloc((size_t)length);
    if (bytes == NULL || fread(bytes, 1, (size_t)length, file) != (size_t)length) {
        free(bytes); fclose(file); return NULL;
    }
    fclose(file);
    *size = (size_t)length;
    return bytes;
}

static int digest_frames(gbb_instance *machine, uint64_t *hash) {
    uint16_t pixels[GBB_FRAME_PIXELS];
    gbb_frame_info info;
    for (unsigned frame = 0; frame < 30u; ++frame) {
        gbb_audio_frame audio[1024];
        size_t count = 0;
        gbb_run_result result = gbb_run_audio(machine, FRAME_HALF_DOTS,
            audio, sizeof(audio) / sizeof(audio[0]), &count);
        REQUIRE(result.reason == GBB_STOP_BUDGET ||
                result.reason == GBB_STOP_HALTED_IDLE ||
                result.reason == GBB_STOP_OUTPUT_FULL);
        for (;;) {
            for (size_t i = 0; i < count; ++i) {
                const uint16_t left = (uint16_t)audio[i].left;
                const uint16_t right = (uint16_t)audio[i].right;
                const uint8_t pcm[4] = {(uint8_t)left, (uint8_t)(left >> 8),
                                        (uint8_t)right, (uint8_t)(right >> 8)};
                hash_bytes(hash, pcm, sizeof(pcm));
            }
            if (result.reason != GBB_STOP_OUTPUT_FULL) break;
            result = gbb_run_audio(machine, FRAME_HALF_DOTS - result.consumed_half_dots,
                audio, sizeof(audio) / sizeof(audio[0]), &count);
            REQUIRE(result.reason == GBB_STOP_BUDGET ||
                    result.reason == GBB_STOP_HALTED_IDLE ||
                    result.reason == GBB_STOP_OUTPUT_FULL);
        }
        if (gbb_copy_frame_rgb555(machine, pixels, sizeof(pixels),
                GBB_FRAME_WIDTH * sizeof(uint16_t), &info) == GBB_OK) {
            for (size_t p = 0; p < sizeof(pixels) / sizeof(pixels[0]); ++p) {
                const uint8_t rgb[2] = {(uint8_t)pixels[p], (uint8_t)(pixels[p] >> 8)};
                hash_bytes(hash, rgb, sizeof(rgb));
            }
        }
    }
    return 0;
}

static int pin_rom(const char *path, uint64_t *digest) {
    size_t rom_size = 0;
    uint8_t *rom = read_file(path, &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    *digest = FNV_OFFSET;
    int rc = digest_frames(machine, digest);
    gbb_destroy(machine);
    free(rom);
    return rc;
}

static int inline_guest(uint64_t *digest) {
    uint8_t rom[32768] = {0};
    rom[0x143] = 0xC0;
    rom[0x147] = 0;
    rom[0x148] = 0;
    rom[0x149] = 0;
    const uint8_t setup[] = {
        0x3E,0x05,0xE0,0x07, 0x3E,0xA5,0xE0,0x01, 0x3E,0x81,0xE0,0x02,
        0xC3,0x50,0x01
    };
    const uint8_t code[] = {
        0x3E,0xC0,0xE0,0x46, 0x21,0x00,0xC0, 0x06,0x40,
        0xF0,0x04,0x22, 0xF0,0x05,0x22, 0xF0,0x01,0x22, 0xF0,0x02,0x22,
        0xF0,0x0F,0x22, 0x05,0x20,0xEE, 0x18,0xFE
    };
    memcpy(rom + 0x100, setup, sizeof(setup));
    memset(rom + 0x150, 0x00, 4096u);
    memcpy(rom + 0x1150, code, sizeof(code));
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    gbb_run_result run = gbb_run(machine, UINT64_C(200000), NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    gbb_trace_record snapshot;
    memset(&snapshot, 0, sizeof(snapshot));
    gbb_test_cpu_snapshot(machine, &snapshot);
    *digest = FNV_OFFSET;
    hash_bytes(digest, &snapshot, sizeof(snapshot));
    hash_bytes(digest, machine->wram[0], 320u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_identity_pin(const char *root, int flip) {
    char path[1024];
    int mismatch = 0;
    for (size_t i = 0; i < sizeof(SPEED_PINS) / sizeof(SPEED_PINS[0]) - 1u; ++i) {
        (void)snprintf(path, sizeof(path), "%s/%s", root, SPEED_PINS[i].path);
        uint64_t actual = 0;
        REQUIRE(pin_rom(path, &actual) == 0);
        const uint64_t expected = SPEED_PINS[i].digest ^ (flip ? UINT64_C(1) : UINT64_C(0));
        if (actual != expected) {
            fprintf(stderr, "observed %s %016llx\n", SPEED_PINS[i].path,
                    (unsigned long long)actual);
            mismatch = 1;
        }
    }
    uint64_t actual = 0;
    REQUIRE(inline_guest(&actual) == 0);
    const uint64_t expected = SPEED_PINS[7].digest ^ (flip ? UINT64_C(1) : UINT64_C(0));
    if (actual != expected) {
        fprintf(stderr, "observed %s %016llx\n", SPEED_PINS[7].path,
                (unsigned long long)actual);
        mismatch = 1;
    }
    return mismatch;
}

static int cgb_speed_internal_harness_alive(void) {
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    gbb_destroy(machine);
    return 0;
}

static int run_tracer_guest(int with_trace) {
    _Static_assert(sizeof(gbb_trace_record) == 24u,
                   "trace record has no speed field (D-13)");
    uint8_t rom[32768] = {0};
    rom[0x143] = 0xC0;
    rom[0x147] = 0u;
    rom[0x148] = 0u;
    rom[0x149] = 0u;
    const uint8_t code[] = {
        0x3E,0x01, 0xE0,0x4D, 0xF0,0x4D, 0xEA,0x00,0xC0,
        0x10,0x00, 0xF0,0x4D, 0xEA,0x01,0xC0, 0xF0,0x04,
        0xEA,0x02,0xC0, 0x76
    };
    memcpy(rom + 0x100, code, sizeof(code));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);

    gbb_trace_record records[16];
    size_t traced = 0u;
    gbb_trace_record *trace = with_trace ? records : NULL;
    size_t capacity = with_trace ? 16u : 0u;
    const uint64_t want_to_double = GBB_SPEED_SWITCH_STALL_T * GBB_HALF_DOTS_PER_T_DOUBLE;
    gbb_run_result result = gbb_run(machine, 112u, trace, capacity);
    REQUIRE(!machine->stopped);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 112u);
    traced += result.trace_count;
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x7Fu);
    uint8_t speed = 0u, kind = 0u, armed = 0u;
    uint32_t remaining = 0u;
    gbb_test_speed_state(machine, &speed, &kind, &remaining, &armed);
    REQUIRE(speed == 1u && kind == GBB_STALL_SPEED_SWITCH && armed == 0u);
    REQUIRE(remaining == want_to_double && machine->divider_counter == 0u && !machine->stopped);

    result = gbb_run(machine, 1000u, trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 1000u);
    REQUIRE(result.trace_count == 0u);
    traced += result.trace_count;
    result = gbb_run(machine, 3u, trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
    REQUIRE(result.trace_count == 0u);
    traced += result.trace_count;
    result = gbb_run(machine, want_to_double - 1000u,
                     trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_BUDGET &&
            result.consumed_half_dots == want_to_double - 1000u);
    REQUIRE(result.trace_count == 0u);
    traced += result.trace_count;
    REQUIRE(machine->time_half_dots == 112u + want_to_double);
    REQUIRE(machine->divider_counter != 0u);
    gbb_test_speed_state(machine, &speed, &kind, &remaining, &armed);
    REQUIRE(speed == 1u && kind == GBB_STALL_NONE && remaining == 0u && armed == 0u);

    result = gbb_run(machine, 60u, trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_HALTED_IDLE && result.consumed_half_dots == 60u);
    traced += result.trace_count;
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFEu);
    if (with_trace) {
        unsigned stops = 0u;
        for (size_t i = 0; i < traced; ++i)
            if (records[i].opcode_size != 0u && records[i].opcode[0] == 0x10u) ++stops;
        REQUIRE(traced == 10u && stops == 1u);
    }
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_tracer_switch(void) {
    REQUIRE(run_tracer_guest(0) == 0);
    REQUIRE(run_tracer_guest(1) == 0);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
#ifdef GBB_P12_MUTANT_BUILD
    if (argc >= 4 && strcmp(argv[argc - 2], "--mutants") == 0) {
        char *end = NULL;
        errno = 0;
        unsigned long long mask = strtoull(argv[argc - 1], &end, 0);
        if (errno != 0 || end == argv[argc - 1] || *end != '\0') return 2;
        gbb_p12_mutants = (uint64_t)mask;
        argc -= 2;
    }
#else
    for (int i = 2; i < argc; ++i)
        if (strcmp(argv[i], "--mutants") == 0) return 2;
#endif
    if (strcmp(argv[1], "cgb_speed_internal_harness_alive") == 0) {
        int rc = cgb_speed_internal_harness_alive();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_internal_harness_alive pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_identity_pin") == 0) {
        if (argc < 3 || argc > 4) return 2;
        const int flip = argc == 4 && strcmp(argv[3], "--flip") == 0;
        if (argc == 4 && !flip) return 2;
        int rc = cgb_speed_identity_pin(argv[2], flip);
        if (rc == 0) puts("cgb-speed-internal cgb_speed_identity_pin pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_tracer_switch") == 0) {
        int rc = cgb_speed_tracer_switch();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_tracer_switch pass");
        return rc;
    }
    return 2;
}
