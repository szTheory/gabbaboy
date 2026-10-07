#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

static uint8_t *read_rom(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (!f || fseek(f, 0, SEEK_END) != 0) return NULL;
    long n = ftell(f);
    if (n < 0 || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    uint8_t *p = malloc((size_t)n);
    if (!p || fread(p, 1, (size_t)n, f) != (size_t)n) { free(p); fclose(f); return NULL; }
    fclose(f); *size = (size_t)n; return p;
}

static int visible_composition(const char *path) {
    size_t size = 0;
    uint8_t *rom = read_rom(path, &size);
    REQUIRE(rom != NULL);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
    gbb_run_result run = gbb_run(m, UINT64_C(180000), NULL, 0);
    uint8_t pixels[160u * 144u];
    gbb_frame_info info = {0};
    gbb_error frame_error = gbb_copy_frame(m, pixels, sizeof(pixels), 160, &info);
    if (frame_error != GBB_OK) fprintf(stderr, "frame copy returned %d\n", frame_error);
    REQUIRE(frame_error == GBB_OK);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(info.width == 160 && info.height == 144 && info.generation != 0);
    REQUIRE(info.completion_half_dots <= run.consumed_half_dots);
    for (unsigned y = 0; y < 144; ++y) {
        for (unsigned x = 0; x < 160; ++x) {
            uint8_t expected = x < 8 && y < 8 ? 1u : 0u;
            REQUIRE(pixels[y * 160u + x] == expected);
        }
    }
    gbb_destroy(m);
    free(rom);
    return 0;
}

static int visible_gameplay(const char *path) {
    size_t size = 0;
    uint8_t *rom = read_rom(path, &size);
    REQUIRE(rom != NULL);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
    gbb_run_result run = gbb_run(m, UINT64_C(180000), NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    uint64_t base = run.consumed_half_dots;
    const gbb_input_event events[] = {
        {base + 8u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {base + 50008u, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    REQUIRE(gbb_queue_events(m, events, 2) == GBB_OK);
    run = gbb_run(m, UINT64_C(280000), NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    uint8_t pixels[160u * 144u];
    gbb_frame_info info = {0};
    REQUIRE(gbb_copy_frame(m, pixels, sizeof(pixels), 160, &info) == GBB_OK);
    REQUIRE(gbb_peek_ram(m, 0xC000) == 1 && gbb_peek_ram(m, 0xC001) == 1);
    REQUIRE(pixels[0] == 1u);
    gbb_destroy(m);
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    if (strcmp(argv[1], "frame_composition_tracer") == 0)
        return visible_composition(argv[2]);
    if (strcmp(argv[1], "joypad_gameplay_tracer") == 0)
        return visible_gameplay(argv[2]);
    size_t size = 0; uint8_t *rom = read_rom(argv[2], &size);
    REQUIRE(rom != NULL);
    if (strcmp(argv[1], "failure") == 0) rom[0x154] = 0x00; /* Guest stores/reads the wrong RAM value. */
    /* Historical case name retained: D3 is an unused SM83 encoding and locks up. */
    if (strcmp(argv[1], "unsupported") == 0) rom[0x150] = 0xD3;
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
    gbb_trace_record *trace = calloc(16384, sizeof(*trace));
    REQUIRE(trace != NULL);
    size_t capacity = strcmp(argv[1], "trace") == 0 ? 1 : 16384;
    uint64_t budget = strcmp(argv[1], "timeout") == 0 ? 1 : UINT64_C(200000);
    gbb_run_result r = gbb_run(m, budget, trace, capacity);
    uint8_t marker = gbb_peek_ram(m, 0xC001);
    if (strcmp(argv[1], "success") == 0) {
        REQUIRE(marker == 0xA5 && r.reason == GBB_STOP_BUDGET && r.trace_count > 0);
    } else if (strcmp(argv[1], "failure") == 0) {
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0x00);
        REQUIRE(marker == 0xEE && marker != 0xA5);
    } else if (strcmp(argv[1], "unsupported") == 0) {
        REQUIRE(r.reason == GBB_STOP_LOCKUP && r.lockup_pc == 0x150 && r.lockup_opcode == 0xD3 && marker != 0xA5);
    } else if (strcmp(argv[1], "timeout") == 0) {
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && marker == 0);
    } else if (strcmp(argv[1], "trace") == 0) {
        REQUIRE(r.reason == GBB_STOP_TRACE_FULL && r.trace_count == 1 && marker != 0xA5);
    } else return 2;
    gbb_destroy(m); free(trace); free(rom); return 0;
}
