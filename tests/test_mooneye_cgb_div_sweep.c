#include "../src/core/gabbaboy.c"

#include <stdio.h>
#include <stdlib.h>

/* Single-TU white-box test: it includes the core source to reach the instance layout, so it must not
 * link GabbaBoy::core (duplicate definitions).
 *
 * A1: the compat-mode DIV phase (divider_counter 0x2678) is a post-boot table cell. Plan 10-06 froze it
 * with an original guest tuned to the same timing; this test re-runs the sweep on the real derived
 * Mooneye ROM fixtures/mooneye-cgb/boot_div-cgbABCDE.gb, so the cell is confirmed (or refuted) by the
 * hardware-derived ROM rather than by a guest written to agree with it. For every starting divider_counter
 * 0x2670..0x2680 and both divider_phase values the ROM is run from its entry, and a start counts as passing
 * when the ROM reaches its LD B,B result with the Mooneye pass registers 3, 5, 8, 13, 21, 34 after the
 * assert callback ran (the runner's own predicate). The passing set must be exactly 0x2678..0x267B.
 *
 * Usage: test_mooneye_cgb_div_sweep <rom.gb> <callback_pc_hex> <result_pc_hex> [--expect-first <hex>]
 * --expect-first moves the asserted window start; it exists only so a negative control can prove a
 * mis-placed window is reported. */

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define HALF_DOT_BUDGET UINT64_C(2000000)
#define SWEEP_FIRST 0x2670u
#define SWEEP_LAST 0x2680u
#define CHUNK UINT64_C(2048)
#define TRACE_N 128u

static const uint8_t pass_registers[6] = {3u, 5u, 8u, 13u, 21u, 34u};

/* Run the loaded ROM until its LD B,B result, then classify. Returns 1 pass, 0 not a pass (wrong
 * registers, or the callback/result was never reached inside the budget), -1 on a harness fault. */
static int classify(gbb_instance *m, uint16_t callback_pc, uint16_t result_pc, int *reached_out) {
    gbb_trace_record trace[TRACE_N];
    uint64_t ticks = 0u;
    int callback_seen = 0;
    *reached_out = 0;
    while (ticks < HALF_DOT_BUDGET) {
        const gbb_run_result r = gbb_run(m, CHUNK, trace, TRACE_N);
        ticks += r.consumed_half_dots;
        for (size_t i = 0u; i < r.trace_count; ++i) {
            if (trace[i].pc == callback_pc) callback_seen = 1;
            if (trace[i].pc == result_pc && trace[i].opcode[0] == 0x40u) {
                const uint8_t got[6] = {trace[i].b, trace[i].c, trace[i].d,
                                        trace[i].e, trace[i].h, trace[i].l};
                *reached_out = 1;
                return callback_seen && memcmp(got, pass_registers, sizeof(got)) == 0;
            }
        }
        if (r.reason == GBB_STOP_TRACE_FULL) continue;
        if (r.reason != GBB_STOP_BUDGET) return 0; /* a core stop: the ROM did not finish */
        if (r.consumed_half_dots == 0u) return -1;
    }
    return 0;
}

static gbb_instance *load_rom_file(const char *path) {
    static uint8_t rom[0x8000 + 1];
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    const size_t n = fread(rom, 1u, sizeof(rom), f);
    const int failed = ferror(f);
    fclose(f);
    if (failed || n != 0x8000u) return NULL;
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &m) != GBB_OK || gbb_load_rom(m, rom, n) != GBB_OK) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

static int parse_hex(const char *text, unsigned *out) {
    char *end = NULL;
    const unsigned long value = strtoul(text, &end, 16);
    if (end == text || *end != '\0' || value > 0xFFFFu) return 0;
    *out = (unsigned)value;
    return 1;
}

int main(int argc, char **argv) {
    unsigned callback = 0u, result = 0u, expect_first = 0x2678u;
    if (argc != 4 && argc != 6) {
        fprintf(stderr, "usage: test_mooneye_cgb_div_sweep <rom.gb> <callback_pc_hex> <result_pc_hex> [--expect-first <hex>]\n");
        return 2;
    }
    if (!parse_hex(argv[2], &callback) || !parse_hex(argv[3], &result)) { fprintf(stderr, "bad pc\n"); return 2; }
    if (argc == 6) {
        if (strcmp(argv[4], "--expect-first") != 0 || !parse_hex(argv[5], &expect_first)) { fprintf(stderr, "bad option\n"); return 2; }
    }

    /* The default compat instance, with no override, must pass: the table cell is inside the window. */
    {
        gbb_instance *m = load_rom_file(argv[1]);
        REQUIRE(m != NULL);
        REQUIRE(m->divider_counter == 0x2678u && m->divider_phase == 0u);
        int reached = 0;
        const int ok = classify(m, (uint16_t)callback, (uint16_t)result, &reached);
        REQUIRE(reached);
        REQUIRE(ok == 1);
        gbb_destroy(m);
        printf("ok 1 - default compat instance passes boot_div-cgbABCDE\n");
    }

    unsigned long long all_passing = 0u;
    for (unsigned phase = 0u; phase < 2u; ++phase) {
        unsigned long long passing = 0u;
        unsigned reached_count = 0u;
        for (unsigned counter = SWEEP_FIRST; counter <= SWEEP_LAST; ++counter) {
            gbb_instance *m = load_rom_file(argv[1]);
            REQUIRE(m != NULL);
            /* After the load's reset, override the divider the way the post-boot row seeds it. */
            m->divider_counter = (uint16_t)counter;
            m->div = (uint8_t)(counter >> 8);
            m->divider_phase = (uint8_t)phase;
            int reached = 0;
            const int ok = classify(m, (uint16_t)callback, (uint16_t)result, &reached);
            REQUIRE(ok >= 0);
            reached_count += (unsigned)reached;
            if (ok == 1) passing |= 1ull << (counter - SWEEP_FIRST);
            gbb_destroy(m);
        }
        /* Every start must finish with a verdict; a ROM that hangs would read as "not passing" otherwise. */
        REQUIRE(reached_count == SWEEP_LAST - SWEEP_FIRST + 1u);
        printf("phase %u passing set mask 0x%llX (counter 0x%X + bit)\n", phase, passing, SWEEP_FIRST);
        const unsigned long long expected_mask = 0xFull << (expect_first - SWEEP_FIRST);
        if (passing != expected_mask) {
            fprintf(stderr, "passing set mismatch: phase %u observed mask 0x%llX, expected counters 0x%X..0x%X (mask 0x%llX)\n",
                    phase, passing, expect_first, expect_first + 3u, expected_mask);
            return 1;
        }
        all_passing |= passing;
    }
    REQUIRE(all_passing == 0xFull << (expect_first - SWEEP_FIRST));
    printf("ok 2 - passing set is exactly 0x%X..0x%X for both divider phases\n", expect_first, expect_first + 3u);
    return 0;
}
