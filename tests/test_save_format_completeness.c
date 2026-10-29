/* Phase 18, HOST-03, D-20: enumerate every cartridge the core admits, in process.
 *
 * For each header cartridge type ($147) x RAM code ($149, 0..5) x ROM code ($148, 0..8) this builds a header-valid
 * ROM and asks the core through the public API (gbb_probe_rom, then gbb_load_rom + gbb_battery_size for the
 * cross-check). It prints one line per admitted combination:
 *
 *   admitted type=0xTT ram=0xRR rom=0xCC battery=0|1 bytes=<n> rtc=0|1
 *   admitted-done count=<n>
 *
 * where bytes is the raw .sav size for a battery cartridge (cartridge RAM plus the 21-byte RTC block) and 0
 * otherwise. tests/scripts/verify-save-formats.py --check-completeness reads this output and holds
 * docs/host-contract.json to it in both directions: every admitted battery combination has a row and every row
 * is admitted. One enumeration replaces thousands of runner spawns. Links only GabbaBoy::core.
 *
 * MBC30 ($10 with RAM code $05) is not admitted, and this program refuses to run if the core ever admits it. */
#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RAM_CODES 6u
#define ROM_CODES 9u
#define MAX_ROM_BYTES ((size_t)32768u << 8)

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* One shared zeroed buffer: only the four header bytes differ between combinations, and the ROM size passed to
 * the core is 32 KiB << rom code, so no per-combination allocation or clearing is needed. */
static void set_header(uint8_t *rom, unsigned type, unsigned ram_code, unsigned rom_code) {
    rom[0x147u] = (uint8_t)type;
    rom[0x148u] = (uint8_t)rom_code;
    rom[0x149u] = (uint8_t)ram_code;
    fix_checksum(rom);
}

/* The load path must agree with the probe on admission and on the battery image size. */
static int cross_check(const uint8_t *rom, unsigned type, unsigned ram_code, unsigned rom_code,
                       const gbb_info *info, int expect_loaded, size_t expect_bytes) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) {
        printf("FAIL battery-size create type=0x%02X\n", type);
        return 1;
    }
    const size_t rom_size = (size_t)32768u << rom_code;
    const gbb_error loaded = gbb_load_rom(machine, rom, rom_size);
    int failed = 0;
    if ((loaded == GBB_OK) != (expect_loaded != 0)) {
        printf("FAIL battery-size load disagrees with probe type=0x%02X ram=0x%02X rom=0x%02X\n", type, ram_code,
               rom_code);
        failed = 1;
    } else if (loaded == GBB_OK) {
        size_t bytes = 0u;
        const gbb_error sized = gbb_battery_size(machine, &bytes);
        if ((info->flags & GBB_INFO_HAS_BATTERY) != 0u) {
            if (sized != GBB_OK || bytes != expect_bytes) {
                printf("FAIL battery-size type=0x%02X ram=0x%02X rom=0x%02X probe=%zu battery_size=%zu\n", type,
                       ram_code, rom_code, expect_bytes, bytes);
                failed = 1;
            }
        } else if (sized == GBB_OK) {
            printf("FAIL battery-size type=0x%02X ram=0x%02X rom=0x%02X has no battery but reports a size\n", type,
                   ram_code, rom_code);
            failed = 1;
        }
    }
    gbb_destroy(machine);
    return failed;
}

int main(void) {
    uint8_t *rom = calloc(MAX_ROM_BYTES, 1u);
    if (rom == NULL) {
        printf("FAIL allocation\n");
        return 1;
    }
    unsigned count = 0u;
    for (unsigned type = 0u; type < 256u; ++type) {
        for (unsigned ram_code = 0u; ram_code < RAM_CODES; ++ram_code) {
            for (unsigned rom_code = 0u; rom_code < ROM_CODES; ++rom_code) {
                set_header(rom, type, ram_code, rom_code);
                gbb_info info;
                memset(&info, 0, sizeof(info));
                info.struct_size = (uint32_t)sizeof(info);
                const gbb_error probed =
                    gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, rom, (size_t)32768u << rom_code, &info);
                const int admitted = probed == GBB_OK;
                const int battery = admitted && (info.flags & GBB_INFO_HAS_BATTERY) != 0u;
                const int rtc = admitted && (info.flags & GBB_INFO_HAS_RTC) != 0u;
                const size_t bytes = battery ? (size_t)info.ram_size_bytes + (rtc ? GBB_RTC_BLOCK_SIZE : 0u) : 0u;
                if (admitted && type == 0x10u && ram_code == 0x05u) {
                    printf("FAIL mbc30-admitted type=0x10 ram=0x05 rom=0x%02X\n", rom_code);
                    free(rom);
                    return 1;
                }
                /* The load-path cross-check covers ROM code 0 of every admitted combination, plus the MBC1
                 * 32 KiB RAM boundary (ROM codes 4 and 5): $03/$03 is admitted at 4 and refused at 5. */
                const int boundary = type == 0x03u && ram_code == 0x03u && (rom_code == 4u || rom_code == 5u);
                if ((rom_code == 0u && admitted) || boundary) {
                    if (cross_check(rom, type, ram_code, rom_code, &info, admitted, bytes) != 0) {
                        free(rom);
                        return 1;
                    }
                }
                if (!admitted) continue;
                printf("admitted type=0x%02X ram=0x%02X rom=0x%02X battery=%d bytes=%zu rtc=%d\n", type, ram_code,
                       rom_code, battery, bytes, rtc);
                ++count;
            }
        }
    }
    printf("admitted-done count=%u\n", count);
    free(rom);
    return 0;
}
