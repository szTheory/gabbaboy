/* Public guest-level CGB HDMA scheduler regressions (Phase 13, D-08/D-10/D-14).
 * The guest is an inline original ROM image and all observations come through the public API. */
#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

#define ROM_SIZE 32768u
#define HALT_WAKE_BUDGET 60000u

static void fix_header_checksum(uint8_t *rom) {
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

static void build_halt_wake_rom(uint8_t rom[ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3E,0x02,0xE0,0x51,       /* FF51 = $02 */
        0x3E,0x00,0xE0,0x52,       /* FF52 = $00 */
        0x3E,0x00,0xE0,0x53,       /* FF53 = $00 */
        0x3E,0x00,0xE0,0x54,       /* FF54 = $00 */
        0x3E,0x82,0xE0,0x55,       /* three HBlank blocks */
        0x3E,0x04,0xEA,0xFF,0xFF, /* IE = timer */
        0xAF,0xE0,0x0F,             /* clear IF */
        0xAF,0xE0,0x05,             /* TIMA = 0 */
        0xAF,0xE0,0x06,             /* TMA = 0 */
        0x3E,0x05,0xE0,0x07,       /* timer on, 16 T period */
        0xFB,0x00,0x76,             /* EI; retire; HALT across visible HBlanks */
        0xF0,0x55,0xFE,0xFF,0x20,0xFA, /* poll FF55 until all blocks finish */
        0x21,0x00,0x80,             /* HL = VRAM source */
        0x11,0x00,0xC2,             /* DE = WRAM readback */
        0x06,0x30,                  /* B = 48 bytes */
        0x2A,0x12,0x13,0x05,0x20,0xFB, /* copy bytes to WRAM */
        0x76
    };
    static const uint8_t timer_vector[] = {
        0xF0,0x55,0xEA,0x00,0xC1, /* store FF55 at wake */
        0x3E,0x5A,0xEA,0x01,0xC1, /* mark real timer-vector dispatch */
        0xAF,0xE0,0x07,0xD9       /* stop timer and RETI */
    };

    memset(rom, 0, ROM_SIZE);
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = 0x80u;
    memcpy(rom + 0x150u, program, sizeof(program));
    memcpy(rom + 0x50u, timer_vector, sizeof(timer_vector));
    for (unsigned i = 0u; i < 48u; ++i) rom[0x200u + i] = (uint8_t)(0x31u + i);
    fix_header_checksum(rom);
}

static int run_halt_wake(int use_run_ex) {
    uint8_t rom[ROM_SIZE];
    build_halt_wake_rom(rom);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK) return 1;
    if (gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return 1;
    }
    uint64_t remaining = HALT_WAKE_BUDGET;
    while (remaining != 0u) {
        const gbb_run_result run = use_run_ex
            ? gbb_run_ex(machine, remaining, NULL, 0u, NULL, 0u)
            : gbb_run(machine, remaining, NULL, 0u);
        if (run.consumed_half_dots == 0u || run.consumed_half_dots > remaining ||
            run.reason == GBB_STOP_UNSUPPORTED_BUS || run.reason == GBB_STOP_LOCKUP ||
            run.reason == GBB_STOP_INVALID_STATE) {
            fprintf(stderr, "guest halt: run consumed=%llu remaining=%llu reason=%d\n",
                    (unsigned long long)run.consumed_half_dots,
                    (unsigned long long)remaining, (int)run.reason);
            gbb_destroy(machine);
            return 1;
        }
        remaining -= run.consumed_half_dots;
    }

    const uint8_t status_at_wake = gbb_peek_ram(machine, 0xC100u);
    const uint8_t dispatched = gbb_peek_ram(machine, 0xC101u);
    if (status_at_wake != 0x02u) {
        fprintf(stderr, "guest halt: wake FF55 expected=02 actual=%02X\n", status_at_wake);
        gbb_destroy(machine);
        return 1;
    }
    if (dispatched != 0x5Au) {
        fprintf(stderr, "guest halt: timer vector marker expected=5A actual=%02X\n", dispatched);
        gbb_destroy(machine);
        return 1;
    }
    if (gbb_peek_ram(machine, 0xFF55u) != 0xFFu) {
        fprintf(stderr, "guest halt: resumed guest did not finish remaining HBlank blocks\n");
        gbb_destroy(machine);
        return 1;
    }
    for (unsigned i = 0u; i < 48u; ++i) {
        const uint8_t actual = gbb_peek_ram(machine, (uint16_t)(0xC200u + i));
        const uint8_t expected = (uint8_t)(0x31u + i);
        if (actual != expected) {
            fprintf(stderr, "guest halt: readback[%u] expected=%02X actual=%02X\n",
                    i, expected, actual);
            gbb_destroy(machine);
            return 1;
        }
    }
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "guest_halt") == 0) {
        if (run_halt_wake(0) != 0) return 1;
        puts("cgb-hdma guest_halt pass");
        return 0;
    }
    fprintf(stderr, "usage: test_cgb_hdma guest_halt\n");
    return 2;
}
