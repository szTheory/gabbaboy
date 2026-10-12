#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "gabbaboy/gabbaboy.h"

int gbb_fuzz_core_one_input(const uint8_t *data, size_t size);
extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);

/* cgb_fuzz_io_regressions (D-27): CGB-profile seeds only. data[0] bit 7 selects the CGB profile,
 * bit 6 the guest I/O path. Each guest operation is selector, value, address. */
static int run_cgb_seeds(void) {
    /* SVBK <- 0 (selects 1), VBK <- 1, SVBK <- 6, then read both back and a fuzzed address. */
    static const uint8_t seed_bank_writes[] = {
        0xC0u, 0x01u,
        0x02u, 0x00u, 0x00u,
        0x06u, 0x01u, 0x00u,
        0x02u, 0x06u, 0x00u,
        0x03u, 0x00u, 0x00u,
        0x07u, 0x00u, 0x00u,
        0x00u, 0xFFu, 0x44u
    };
    /* Wide sweep: LCDC/DMA/boot/KEY1/DIV and the VRAM-DMA registers with 0xFF values. */
    static const uint8_t seed_wide[] = {
        0xC0u, 0x01u,
        0x00u, 0xFFu, 0x40u,  0x00u, 0xFFu, 0x46u,  0x00u, 0xFFu, 0x50u,  0x00u, 0xFFu, 0x4Du,
        0x00u, 0xFFu, 0x04u,  0x00u, 0xFFu, 0x51u,  0x00u, 0xFFu, 0x55u,  0x01u, 0x00u, 0x68u,
        0x00u, 0x07u, 0x70u,  0x02u, 0x07u, 0x00u,  0x00u, 0x00u, 0x7Fu,  0x01u, 0x00u, 0x00u
    };
    /* PGB-flagged $143 on the CGB profile through the synthesised-length loader path. */
    static const uint8_t seed_pgb[] = {0x82u, 0x10u, 0x00u, 0x00u, 0x00u, 0x00u, 0x84u};
    static const uint8_t seed_c0[] = {0x82u, 0x10u, 0x00u, 0x00u, 0x00u, 0x00u, 0xC0u};
    static const uint8_t seed_cgb_stateful[] = {0x83u, 0x03u, 0x04u, 0x03u, 0x00u, 0x03u};
    static const uint8_t seed_cgb_loader[] = {0x80u, 0x00u, 0x01u};
    if (gbb_fuzz_core_one_input(seed_bank_writes, sizeof(seed_bank_writes)) != 0 ||
        gbb_fuzz_core_one_input(seed_wide, sizeof(seed_wide)) != 0 ||
        gbb_fuzz_core_one_input(seed_pgb, sizeof(seed_pgb)) != 0 ||
        gbb_fuzz_core_one_input(seed_c0, sizeof(seed_c0)) != 0 ||
        gbb_fuzz_core_one_input(seed_cgb_stateful, sizeof(seed_cgb_stateful)) != 0 ||
        gbb_fuzz_core_one_input(seed_cgb_loader, sizeof(seed_cgb_loader)) != 0) {
        fprintf(stderr, "CGB fuzz seed failed\n");
        return 1;
    }

    /* Control: the seam the fuzz invariant reads really reflects guest bank writes, so the
     * invariant is not vacuous. A guest that writes VBK=1 and SVBK=5 must show (1, 5). */
    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3u; rom[0x101] = 0x50u; rom[0x102] = 0x01u;
    static const uint8_t program[] = {0x3Eu, 0x01u, 0xE0u, 0x4Fu, 0x3Eu, 0x05u, 0xE0u, 0x70u, 0x76u};
    memcpy(rom + 0x150, program, sizeof(program));
    rom[0x143] = 0x80u;
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
    gbb_instance *machine = NULL;
    uint8_t vram_bank = 0u, wram_bank = 0u;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        fprintf(stderr, "control setup failed\n");
        gbb_destroy(machine);
        return 1;
    }
    (void)gbb_run(machine, 2048u, NULL, 0u);
    gbb_test_bank_state(machine, &vram_bank, &wram_bank);
    gbb_destroy(machine);
    if (vram_bank != 1u || wram_bank != 5u) {
        fprintf(stderr, "bank seam control failed: %u %u\n", vram_bank, wram_bank);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "cgb") == 0) return run_cgb_seeds();
    static const uint8_t dmg_twin_of_minimized[] = {
        0x7Fu, 0x00u, 0x00u, 0x08u, 0x00u,
        0x00u, 0x1Cu, 0x00u, 0x08u, 0x00u
    };
    static const uint8_t minimized_decoder_crash[] = {
        0xFFu, 0x00u, 0x00u, 0x08u, 0x00u,
        0x00u, 0x1Cu, 0x00u, 0x08u, 0x00u
    };
    static const uint8_t seed_declared[] = {0x02u, 0x13u, 0x00u, 0x02u, 0x00u};
    static const uint8_t seed_declared_minus_1[] = {0x02u, 0x10u, 0x01u, 0x03u, 0x01u};
    static const uint8_t seed_declared_plus_1[] = {0x02u, 0x10u, 0x02u, 0x00u, 0x02u};
    static const uint8_t seed_mib2[] = {0x02u, 0x0Fu, 0x06u, 0x00u, 0x03u};
    static const uint8_t seed_mib2_plus_1[] = {0x02u, 0x01u, 0x06u, 0x00u, 0x04u};
    static const uint8_t seed_mib4[] = {0x02u, 0x0Fu, 0x07u, 0x00u, 0x05u};
    static const uint8_t seed_mib4_plus_1[] = {0x02u, 0x10u, 0x07u, 0x02u, 0x06u};
    static const uint8_t seed_mib8[] = {0x02u, 0x19u, 0x08u, 0x00u, 0x07u};
    static const uint8_t seed_mib8_plus_1[] = {0x02u, 0x19u, 0x08u, 0x00u, 0x08u};
    static const uint8_t seed_size_max[] = {0x02u, 0xFFu, 0xFFu, 0xFFu, 0x09u};
    static const uint8_t seed_short[] = {0x02u, 0x10u};
    static const uint8_t over_limit = 0xFFu;
    /* Bit 7 of the first byte now selects the CGB profile, so the original 0xFF reproducer runs on
     * CGB; its bit-7-clear twin keeps the same decoder path on the DMG profile. */
    if (gbb_fuzz_core_one_input(dmg_twin_of_minimized, sizeof(dmg_twin_of_minimized)) != 0) {
        fprintf(stderr, "DMG twin of the minimized reproducer failed\n");
        return 1;
    }
    if (gbb_fuzz_core_one_input(minimized_decoder_crash,
                                sizeof(minimized_decoder_crash)) != 0) {
        fprintf(stderr, "minimized fuzz decoder reproducer failed\n");
        return 1;
    }
    if (gbb_fuzz_core_one_input(NULL, 0u) != 0 ||
        gbb_fuzz_core_one_input(&over_limit, 65537u) != 0) {
        fprintf(stderr, "fuzz input size bounds failed\n");
        return 1;
    }
    if (
        gbb_fuzz_core_one_input(seed_declared, sizeof(seed_declared)) != 0 ||
        gbb_fuzz_core_one_input(seed_declared_minus_1, sizeof(seed_declared_minus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_declared_plus_1, sizeof(seed_declared_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib2, sizeof(seed_mib2)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib2_plus_1, sizeof(seed_mib2_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib4, sizeof(seed_mib4)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib4_plus_1, sizeof(seed_mib4_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib8, sizeof(seed_mib8)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib8_plus_1, sizeof(seed_mib8_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_size_max, sizeof(seed_size_max)) != 0 ||
        gbb_fuzz_core_one_input(seed_short, sizeof(seed_short)) != 0) {
        fprintf(stderr, "synthesised-length fuzz seed failed\n");
        return 1;
    }
    return 0;
}
