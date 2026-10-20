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

int gbb_fuzz_core_last_profile_cgb(void);

/* cgb_fuzz_profile_select (D-27): bit 7 of data[0] must choose the profile the harness creates.
 * Negative control: the CGB seeds and their DMG twins differ only in bit 7, so if selection were
 * fixed to one profile the two observed values would coincide and the equality check fails. */
static int run_profile_select(void) {
    static const uint8_t cgb_loader[] = {0x80u, 0x00u, 0x01u};
    static const uint8_t dmg_loader[] = {0x00u, 0x00u, 0x01u};
    static const uint8_t cgb_io[] = {0xC0u, 0x01u, 0x00u, 0x00u, 0xFFu, 0x44u};
    static const uint8_t dmg_io[] = {0x40u, 0x01u, 0x00u, 0x00u, 0xFFu, 0x44u};
    struct { const uint8_t *data; size_t size; int expect_cgb; const char *name; } cases[] = {
        {cgb_loader, sizeof(cgb_loader), 1, "cgb loader"},
        {dmg_loader, sizeof(dmg_loader), 0, "dmg loader twin"},
        {cgb_io, sizeof(cgb_io), 1, "cgb guest I/O"},
        {dmg_io, sizeof(dmg_io), 0, "dmg twin of guest I/O"},
    };
    int observed[4];
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (gbb_fuzz_core_one_input(cases[i].data, cases[i].size) != 0) {
            fprintf(stderr, "%s: harness rejected input\n", cases[i].name);
            return 1;
        }
        observed[i] = gbb_fuzz_core_last_profile_cgb();
        if (observed[i] != cases[i].expect_cgb) {
            fprintf(stderr, "%s: selected profile cgb=%d, expected %d\n", cases[i].name,
                    observed[i], cases[i].expect_cgb);
            return 1;
        }
    }
    if (observed[0] == observed[1]) {
        fprintf(stderr, "bit 7 did not change the selected profile\n");
        return 1;
    }
    printf("ok 1 - cgb_fuzz_profile_select\n");
    return 0;
}

int gbb_fuzz_core_contract_failures(void);
int gbb_fuzz_core_one_input(const uint8_t *data, size_t size);
void gbb_fuzz_core_speed_observation(int *, uint8_t *, unsigned *, unsigned *,
                                     unsigned *, unsigned *, uint8_t *, uint8_t *,
                                     uint8_t *, uint32_t *, uint32_t *, uint32_t *,
                                     uint64_t *, uint64_t *, uint64_t *, uint32_t *, int *, int *);

/* cgb_fuzz_speed_regressions: a real guest arms KEY1, retires STOP, observes the switched
 * KEY1 value in a later guest store, and maintains exact master-time accounting across slices. */
static int run_speed_seed_case(const uint8_t *seed, size_t seed_size,
                               uint8_t expected_scenario, uint32_t expected_mode,
                               uint32_t expected_profile, unsigned min_switches,
                               unsigned min_reads, uint8_t expected_speed,
                               uint8_t expected_armed, int check_key1,
                               uint8_t expected_key1, uint32_t required_flags,
                               int require_dma_stop, int require_lcd_off) {
    const int failures_before = gbb_fuzz_core_contract_failures();
    if (gbb_fuzz_core_one_input(seed, seed_size) != 0) {
        fprintf(stderr, "speed seed %u was rejected\n", expected_scenario);
        return 1;
    }
    int selected = 0, saw_dma_stop = 0, saw_lcd_off = 0;
    uint8_t scenario = 0u, speed = 0u, armed = 0u, key1 = 0u;
    unsigned switches = 0u, reads = 0u, stops = 0u, calls = 0u;
    uint32_t stall = 0u, mode = 0u, profile = 0u, path_flags = 0u;
    uint64_t consumed = 0u, master_time = 0u, last_trace_time = 0u;
    gbb_fuzz_core_speed_observation(&selected, &scenario, &switches, &reads, &stops, &calls,
                                   &speed, &armed, &key1, &stall, &mode, &profile,
                                   &consumed, &master_time, &last_trace_time, &path_flags,
                                   &saw_dma_stop, &saw_lcd_off);
    if (gbb_fuzz_core_contract_failures() != failures_before || !selected ||
        scenario != expected_scenario || stops == 0u || calls == 0u ||
        switches < min_switches || reads < min_reads || speed != expected_speed ||
        armed != expected_armed || mode != expected_mode || profile != expected_profile ||
        consumed != master_time || consumed > UINT64_C(600000) ||
        last_trace_time > master_time || (path_flags & required_flags) != required_flags ||
        (require_dma_stop && !saw_dma_stop) || (require_lcd_off && !saw_lcd_off) ||
        (check_key1 && key1 != expected_key1)) {
        fprintf(stderr, "speed seed %u positive control failed: selected=%d switches=%u reads=%u "
                        "stops=%u speed=%u armed=%u KEY1=%02X mode=%u profile=%u "
                        "flags=0x%X time=%llu/%llu\n",
                expected_scenario, selected, switches, reads, stops, speed, armed, key1,
                mode, profile, path_flags,
                (unsigned long long)consumed, (unsigned long long)master_time);
        return 1;
    }
    return 0;
}

static int run_speed_seed(void) {
    static const uint8_t seed_arm_and_switch[] = {0x90u, 0x00u, 0x0Fu};
    static const uint8_t seed_switch_every_four[] = {0x90u, 0x01u, 0x0Fu};
    static const uint8_t seed_pending_if[] = {0x90u, 0x02u, 0x0Fu};
    static const uint8_t seed_held_button[] = {0x90u, 0x03u, 0x0Fu};
    static const uint8_t seed_oam_dma[] = {0x90u, 0x04u, 0x0Fu};
    static const uint8_t seed_lcd_off[] = {0x90u, 0x05u, 0x0Fu};
    static const uint8_t seed_compat_twin[] = {0x90u, 0x06u, 0x0Fu};
    static const uint8_t seed_dmg_twin[] = {0x10u, 0x07u, 0x0Fu};
    /* DMG-profile KEY1 scenarios: hosted fuzz run 38947419636 minimized to a 518-byte input
     * (sha256 532b3bf198c578ebf2b97e05415208187a34a8aa5ecd0e5fc96b6609f12f8263) whose decoded
     * prefix is data[0]=0x10 (DMG speed) data[1]=1. The oracle demanded a speed switch on a DMG
     * cartridge. These hand-built equivalents must now fall back to the DMG twin, not fail. */
    static const uint8_t seed_dmg_minimized_prefix[] = {0x10u, 0x01u, 0x00u, 0x02u, 0x03u, 0x04u};
    static const uint8_t seed_dmg_s0[] = {0x10u, 0x00u, 0x0Fu};
    static const uint8_t seed_dmg_s2[] = {0x10u, 0x02u, 0x0Fu};
    static const uint8_t seed_dmg_s4[] = {0x10u, 0x04u, 0x0Fu};
    static const uint8_t seed_dmg_s5[] = {0x10u, 0x05u, 0x0Fu};
    static const uint8_t seed_dmg_s6[] = {0x10u, 0x06u, 0x0Fu};
    static const uint8_t *const dmg_seeds[] = {seed_dmg_minimized_prefix, seed_dmg_s0, seed_dmg_s2,
                                               seed_dmg_s4, seed_dmg_s5, seed_dmg_s6};
    static const size_t dmg_sizes[] = {sizeof(seed_dmg_minimized_prefix), sizeof(seed_dmg_s0),
                                       sizeof(seed_dmg_s2), sizeof(seed_dmg_s4),
                                       sizeof(seed_dmg_s5), sizeof(seed_dmg_s6)};
    for (size_t i = 0u; i < sizeof(dmg_seeds) / sizeof(dmg_seeds[0]); ++i) {
        if (run_speed_seed_case(dmg_seeds[i], dmg_sizes[i], 7u, GBB_MODE_DMG,
                                GBB_PROFILE_DMG_CPU_B, 0u, 0u, 0u, 0u, 0, 0u, 0x00u, 0, 0) != 0) {
            fprintf(stderr, "DMG-profile speed seed %zu failed\n", i);
            return 1;
        }
    }

    if (run_speed_seed_case(seed_arm_and_switch, sizeof(seed_arm_and_switch), 0u,
                            GBB_MODE_CGB, GBB_PROFILE_CGB_CPU_E, 1u, 1u, 1u, 0u,
                            1, 0xFEu, 0x01u, 0, 0) != 0 ||
        run_speed_seed_case(seed_switch_every_four, sizeof(seed_switch_every_four), 1u,
                            GBB_MODE_CGB, GBB_PROFILE_CGB_CPU_E, 2u, 1u, 0u, 0u,
                            0, 0u, 0x01u, 0, 0) != 0 ||
        run_speed_seed_case(seed_pending_if, sizeof(seed_pending_if), 2u,
                            GBB_MODE_CGB, GBB_PROFILE_CGB_CPU_E, 1u, 1u, 1u, 0u,
                            0, 0u, 0x07u, 0, 0) != 0 ||
        run_speed_seed_case(seed_held_button, sizeof(seed_held_button), 3u,
                            GBB_MODE_CGB, GBB_PROFILE_CGB_CPU_E, 0u, 0u, 0u, 1u,
                            0, 0u, 0x0Fu, 0, 0) != 0 ||
        run_speed_seed_case(seed_oam_dma, sizeof(seed_oam_dma), 4u,
                            GBB_MODE_CGB, GBB_PROFILE_CGB_CPU_E, 1u, 1u, 1u, 0u,
                            0, 0u, 0x11u, 1, 0) != 0 ||
        run_speed_seed_case(seed_lcd_off, sizeof(seed_lcd_off), 5u,
                            GBB_MODE_CGB, GBB_PROFILE_CGB_CPU_E, 1u, 1u, 1u, 0u,
                            0, 0u, 0x01u, 0, 1) != 0 ||
        run_speed_seed_case(seed_compat_twin, sizeof(seed_compat_twin), 6u,
                            GBB_MODE_CGB_DMG_COMPAT, GBB_PROFILE_CGB_CPU_E, 0u, 1u, 0u, 0u,
                            1, 0xFFu, 0x01u, 0, 0) != 0 ||
        run_speed_seed_case(seed_dmg_twin, sizeof(seed_dmg_twin), 7u,
                            GBB_MODE_DMG, GBB_PROFILE_DMG_CPU_B, 0u, 0u, 0u, 0u,
                            0, 0u, 0x00u, 0, 0) != 0)
        return 1;
    printf("ok 1 - cgb_fuzz_speed_regressions\n");
    return 0;
}

/* cgb_fuzz_palette_regressions (D-34): palette RAM and compat-palette seeds on the CGB profile.
 * data[0] = 0xA0 selects the palette path and data[1] bit 0 picks CGB mode ($80) or compat mode
 * ($00); then three-byte operations (selector, a, b), see fuzz_core.c. Any violated invariant is
 * counted by the harness, so this returns non-zero when the core breaks one. */
static int run_palette_seeds(void) {
    /* BCPS = $BF (auto-increment, index 63), three BCPD writes wrap the index, then read BCPS. */
    static const uint8_t seed_wrap[] = {
        0xA0u, 0x01u,
        0x00u, 0xBFu, 0x00u,  0x01u, 0x12u, 0x00u,  0x01u, 0x34u, 0x00u,  0x01u, 0x56u, 0x00u,
        0x05u, 0x00u, 0x00u,  0x05u, 0x00u, 0x01u,  0x07u, 0x00u, 0x10u
    };
    /* CRAM writes interleaved with short run slices so some land in mode 3, plus LCD off and on. */
    static const uint8_t seed_mode3[] = {
        0xA0u, 0x01u,
        0x00u, 0x80u, 0x00u,  0x07u, 0x00u, 0x03u,  0x01u, 0xFFu, 0x00u,  0x07u, 0x00u, 0x01u,
        0x01u, 0x7Fu, 0x00u,  0x07u, 0x00u, 0x02u,  0x02u, 0x80u, 0x00u,  0x03u, 0x1Fu, 0x00u,
        0x06u, 0x00u, 0x00u,  0x01u, 0xFFu, 0x00u,  0x06u, 0x91u, 0x00u,  0x04u, 0x01u, 0x00u,
        0x07u, 0x00u, 0x20u
    };
    /* Compat mode: the same palette register traffic plus reads, with DMG-style LCD toggling. */
    static const uint8_t seed_compat[] = {
        0xA0u, 0x00u,
        0x00u, 0x80u, 0x00u,  0x01u, 0xFFu, 0x00u,  0x05u, 0x00u, 0x01u,  0x05u, 0x00u, 0x03u,
        0x06u, 0x00u, 0x00u,  0x06u, 0x91u, 0x00u,  0x07u, 0x00u, 0x40u
    };
    /* Host API: struct_size 27 and 28 each with a bit 15 entry, a valid 29 and 64, NULL, then get. */
    static const uint8_t seed_api[] = {
        0xA0u, 0x01u,
        0x07u, 0x05u, 0x01u,  0x07u, 0x05u, 0x02u,  0x07u, 0x01u, 0x03u,  0x07u, 0x01u, 0x04u,
        0x07u, 0x02u, 0x00u,  0x07u, 0x03u, 0x01u,  0x07u, 0x05u, 0x00u,  0x07u, 0x00u, 0x20u
    };
    /* A seed with no $FFFF word: the mutant must stay quiet on it, so a failure is the mask's. */
    static const uint8_t seed_plain[] = {
        0xA0u, 0x01u,
        0x06u, 0x00u, 0x00u,  0x00u, 0x80u, 0x00u,  0x01u, 0x1Fu, 0x00u,  0x01u, 0x00u, 0x00u,
        0x06u, 0x91u, 0x00u
    };
    static const uint8_t seed_dmg[] = {0x20u, 0x00u, 0x01u, 0x02u};
    static const uint8_t seed_dmg_loader[] = {0x00u, 0x00u, 0x01u};
    gbb_fuzz_core_one_input(seed_wrap, sizeof(seed_wrap));
    gbb_fuzz_core_one_input(seed_mode3, sizeof(seed_mode3));
    gbb_fuzz_core_one_input(seed_compat, sizeof(seed_compat));
    gbb_fuzz_core_one_input(seed_api, sizeof(seed_api));
    gbb_fuzz_core_one_input(seed_plain, sizeof(seed_plain));
    gbb_fuzz_core_one_input(seed_dmg, sizeof(seed_dmg));
    gbb_fuzz_core_one_input(seed_dmg_loader, sizeof(seed_dmg_loader));
    return 0;
}

/* A CRAM colour word of $FFFF in palette 0 colour 0 with the LCD off, then LCD on and two frames. */
static int run_palette_white_word(void) {
    static const uint8_t seed_white[] = {
        0xA0u, 0x01u,
        0x06u, 0x00u, 0x00u,  0x00u, 0x80u, 0x00u,  0x01u, 0xFFu, 0x00u,  0x01u, 0xFFu, 0x00u,
        0x06u, 0x91u, 0x00u
    };
    gbb_fuzz_core_one_input(seed_white, sizeof(seed_white));
    return 0;
}

static int run(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "cgb_profile_select") == 0) return run_profile_select();
    if (argc > 1 && strcmp(argv[1], "cgb") == 0) return run_cgb_seeds();
    if (argc > 1 && strcmp(argv[1], "cgb_speed") == 0) return run_speed_seed();
    if (argc > 1 && strcmp(argv[1], "cgb_palette") == 0) {
        const int rc = run_palette_seeds();
        return rc != 0 ? rc : run_palette_white_word();
    }
    if (argc > 1 && strcmp(argv[1], "cgb_palette_plain") == 0) return run_palette_seeds();
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

int main(int argc, char **argv) {
    const int rc = run(argc, argv);
    if (gbb_fuzz_core_contract_failures() != 0) {
        fprintf(stderr, "fuzz contract failures: %d\n", gbb_fuzz_core_contract_failures());
        return 1;
    }
    return rc;
}
