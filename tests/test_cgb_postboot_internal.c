#include "../src/core/gabbaboy.c"

#include <stdio.h>

/* Single-TU white-box test: it includes the core source to reach the instance layout, so it must
 * not link GabbaBoy::core (duplicate definitions).
 *
 * The compat-mode DIV phase (divider_counter 0x2678, Mooneye boot_div-cgbABCDE) is a post-boot
 * table cell. This test freezes its meaning: an original guest with the same timing as that test
 * (27 NOPs, a DIV read, then NOP groups of 57, 56, 57, 57 and 58 each followed by a DIV read)
 * reads DIV six times, and only a window of four consecutive counter values reproduces the
 * hardware sequence. The sweep proves the cell sits at the start of that window and that both
 * neighbours fail, so a drifted cell cannot pass by accident.
 *
 * The real derived Mooneye ROM is re-swept in Plan 10-16 (A1). */

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define NOPS(n) for (unsigned k_ = 0; k_ < (n); ++k_) code[len++] = 0x00u
/* Each capture is LDH A,(DIV), LD r,A and three padding NOPs, so that with the group NOPs the reads
 * are 64 M-cycles apart, the cadence of the hardware test. */
#define DIV_READ(ld) do { code[len++] = 0xF0u; code[len++] = 0x04u; code[len++] = (ld); \
                          code[len++] = 0x00u; code[len++] = 0x00u; code[len++] = 0x00u; } while (0)

/* Registers B, C, D, E, H, L the guest captures, as the hardware test expects them. */
static const uint8_t expected_div[6] = {0x27u, 0x28u, 0x28u, 0x29u, 0x2Au, 0x2Cu};

static gbb_instance *load_guest(void) {
    static uint8_t rom[0x8000];
    uint8_t code[512];
    unsigned len = 0;
    NOPS(27u);        DIV_READ(0x47u); /* LD B,A */
    NOPS(57u);        DIV_READ(0x4Fu); /* LD C,A */
    NOPS(56u);        DIV_READ(0x57u); /* LD D,A */
    NOPS(57u);        DIV_READ(0x5Fu); /* LD E,A */
    NOPS(57u);        DIV_READ(0x67u); /* LD H,A */
    NOPS(58u);        DIV_READ(0x6Fu); /* LD L,A */
    code[len++] = 0x76u; /* HALT: IE is zero so nothing wakes it */
    memset(rom, 0, sizeof(rom));
    /* Entry is NOP then JP $0150, the usual cartridge entry sequence. */
    rom[0x101] = 0xC3u; rom[0x102] = 0x50u; rom[0x103] = 0x01u;
    memcpy(rom + 0x150, code, len);
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &m) != GBB_OK ||
        gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

/* Returns 1 when the six captured DIV values equal the hardware sequence. */
static int run_guest(gbb_instance *m) {
    const gbb_run_result r = gbb_run(m, 20000u, NULL, 0u);
    if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_HALTED_IDLE) return -1;
    const uint8_t got[6] = {m->b, m->c, m->d, m->e, m->h, m->l};
    return memcmp(got, expected_div, sizeof(got)) == 0;
}

static int div_phase_sweep(void) {
    unsigned passing_mask = 0u;
    for (unsigned phase = 0u; phase < 2u; ++phase) {
        unsigned passing = 0u;
        for (unsigned counter = 0x2670u; counter <= 0x2680u; ++counter) {
            gbb_instance *m = load_guest();
            REQUIRE(m != NULL);
            m->divider_counter = (uint16_t)counter;
            m->div = (uint8_t)(counter >> 8);
            m->divider_phase = (uint8_t)phase;
            const int ok = run_guest(m);
            REQUIRE(ok >= 0);
            if (ok) passing |= 1u << (counter - 0x2670u);
            gbb_destroy(m);
        }
        printf("phase %u passing set mask 0x%X (counter 0x2670 + bit)\n", phase, passing);
        /* Exactly 0x2678..0x267B: bits 8..11 from 0x2670. */
        REQUIRE(passing == 0xF00u);
        passing_mask |= passing;
    }
    REQUIRE(passing_mask == 0xF00u);
    printf("ok 1 - div_phase_sweep\n");
    return 0;
}

/* Without overrides the compat instance passes: the table cell is inside the window. */
static int div_compat_default(void) {
    gbb_instance *m = load_guest();
    REQUIRE(m != NULL);
    REQUIRE(m->divider_counter == 0x2678u && m->divider_phase == 0u && m->div == 0x26u);
    REQUIRE(run_guest(m) == 1);
    gbb_destroy(m);
    printf("ok 1 - div_compat_default\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: test_cgb_postboot_internal <case>\n"); return 2; }
    if (strcmp(argv[1], "div_phase_sweep") == 0) return div_phase_sweep();
    if (strcmp(argv[1], "div_compat_default") == 0) return div_compat_default();
    fprintf(stderr, "unknown case\n");
    return 2;
}
