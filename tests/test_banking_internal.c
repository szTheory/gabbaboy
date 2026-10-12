#include "../src/core/gabbaboy.c"

#include <stdio.h>

/* Single-TU white-box test: it includes the core source to reach the static read8/write8 and the
 * instance layout, so it must not link GabbaBoy::core. The bank-state seam is declared here
 * and not in the public header. */

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define STEPS 200000u

static void make_rom(uint8_t *rom, size_t size, uint8_t cgb_flag) {
    memset(rom, 0, size);
    rom[0x143u] = cgb_flag;
    rom[0x147u] = 0x00u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x00u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static uint64_t rng_next(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    return *state = x;
}

/* Flat 8 KiB WRAM plus 8 KiB VRAM reference, written independently of the banked layout. When
 * `scramble` is set the test pokes the bank fields directly (the guest-visible decode is a later
 * plan). Returns the number of reads that differed from the flat model, or -1 on a hard failure. */
static long run_sequence(gbb_instance *m, int scramble, int expect_pins) {
    static uint8_t ref_wram[8192];
    static uint8_t ref_vram[8192];
    uint64_t rng = UINT64_C(0x9E3779B97F4A7C15);
    long mismatches = 0;
    memset(ref_wram, 0, sizeof(ref_wram));
    memset(ref_vram, 0, sizeof(ref_vram));
    write8(m, 0xFF40u, 0x00u); /* LCD off: VRAM is always accessible */
    /* Zero both models through the bus so the reference starts equal to the core. */
    for (unsigned a = 0xC000u; a <= 0xDFFFu; ++a) write8(m, (uint16_t)a, 0u);
    for (unsigned a = 0x8000u; a <= 0x9FFFu; ++a) write8(m, (uint16_t)a, 0u);
    for (unsigned step = 0; step < STEPS; ++step) {
        if (scramble && step % 10u == 0u) {
            m->wram_bank = (uint8_t)((step / 10u) % 7u + 1u);
            m->vram_bank = (uint8_t)((step / 10u) % 2u);
        }
        uint64_t r = rng_next(&rng);
        unsigned kind = (unsigned)(r % 6u);
        uint8_t value = (uint8_t)(r >> 40);
        unsigned pick = (unsigned)((r >> 8) & 0xFFFFu);
        if (kind < 2u) {
            uint16_t address = (uint16_t)(0xC000u + pick % 0x1E00u);
            unsigned index = (unsigned)address & 0x1FFFu;
            if (kind == 0u) {
                write8(m, address, value);
                ref_wram[index] = value;
            } else if (read8(m, address) != ref_wram[index]) {
                ++mismatches;
            }
        } else if (kind < 4u) {
            uint16_t address = (uint16_t)(0x8000u + pick % 0x2000u);
            unsigned index = address - 0x8000u;
            if (kind == 2u) {
                write8(m, address, value);
                ref_vram[index] = value;
            } else if (read8(m, address) != ref_vram[index]) {
                ++mismatches;
            }
        } else {
            /* FF4F/FF70 are not decoded yet: no-ops on DMG, and not yet routed on CGB either. */
            write8(m, (kind == 4u) ? 0xFF4Fu : 0xFF70u, value);
        }
        if (expect_pins) {
            uint8_t vb = 0xEEu, wb = 0xEEu;
            gbb_test_bank_state(m, &vb, &wb);
            if (vb != 0u || wb != 1u) {
                fprintf(stderr, "bank pins moved at step %u: vram=%u wram=%u\n", step, vb, wb);
                return -1;
            }
        }
    }
    if (expect_pins) {
        for (unsigned a = 0xC000u; a <= 0xFDFFu; ++a) {
            if (gbb_peek_ram(m, (uint16_t)a) != ref_wram[a & 0x1FFFu]) {
                fprintf(stderr, "peek mismatch at %04X\n", a);
                return -1;
            }
        }
    }
    return mismatches;
}

static int banking_dmg_flat_reference(void) {
    static uint8_t rom[0x8000];
    make_rom(rom, sizeof(rom), 0x00u);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    long mismatches = run_sequence(m, 0, 1);
    if (mismatches != 0) fprintf(stderr, "banking flat reference: %ld mismatching reads\n", mismatches);
    REQUIRE(mismatches == 0);
    gbb_destroy(m);
    return 0;
}

static int banking_cgb_diverges_from_flat(void) {
    static uint8_t rom[0x8000];
    make_rom(rom, sizeof(rom), 0x80u);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    long mismatches = run_sequence(m, 1, 0);
    REQUIRE(mismatches >= 0);
    if (mismatches == 0) {
        fprintf(stderr, "banking control: CGB banking did not diverge\n");
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int banking_dmg_bank_pins_after_reset(void) {
    static uint8_t rom[0x8000];
    make_rom(rom, sizeof(rom), 0x00u);
    gbb_instance *m = NULL;
    uint8_t vb = 0xEEu, wb = 0xEEu;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0u && wb == 1u);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0u && wb == 1u);
    m->vram_bank = 1u; m->wram_bank = 5u; m->svbk = 5u; /* disturb, then prove reset restores */
    REQUIRE(gbb_reset(m) == GBB_OK);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0u && wb == 1u && m->svbk == 0u);
    m->vram_bank = 1u; m->wram_bank = 7u;
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0u && wb == 1u);
    gbb_destroy(m);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "banking_dmg_flat_reference") == 0) return banking_dmg_flat_reference();
    if (strcmp(argv[1], "banking_cgb_diverges_from_flat") == 0) return banking_cgb_diverges_from_flat();
    if (strcmp(argv[1], "banking_dmg_bank_pins_after_reset") == 0) return banking_dmg_bank_pins_after_reset();
    return 2;
}
