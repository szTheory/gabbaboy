/* The published save-format ids (Phase 18, HOST-03, D-19).
 *
 * One row per (cartridge type, RAM code, ROM-code constraint) that the core admits with a battery. The table
 * mirrors docs/host-contract.json row for row; tests/scripts/verify-save-formats.py holds the two to each
 * other and to the core, and the id spelling is frozen against the latest release tag. An id names a byte
 * layout: the same id always means the same bytes, so rows may share one (MBC5 with and without rumble).
 * An id carries no release version, no gb/gbc axis and no rumble axis, and it claims no byte
 * interoperability with any other emulator.
 *
 * `none` is not an id. The runner prints `save_format=none bytes=0` for a cartridge without a battery; it is
 * a sentinel that never appears in this table and does not match the id grammar. */
#include "gbb_host.h"

static const host_save_format_row g_rows[] = {
    /* type ram  rom_max               id                                bytes   ram    rtc */
    { 0x03u, 0x02u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc1-sram-8k-v1",       8192u,   8192u,  0u },
    { 0x03u, 0x03u, 0x04u,                    "gabbaboy-mbc1-sram-32k-v1",     32768u,  32768u,  0u },
    { 0x06u, 0x00u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc2-nibble-512-v1",     512u,    512u,  0u },
    { 0x0Fu, 0x00u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc3-rtc-only-v1",        21u,      0u, 21u },
    { 0x10u, 0x02u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc3-rtc-sram-8k-v1",   8213u,   8192u, 21u },
    { 0x10u, 0x03u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc3-rtc-sram-32k-v1", 32789u,  32768u, 21u },
    { 0x13u, 0x02u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc3-sram-8k-v1",       8192u,   8192u,  0u },
    { 0x13u, 0x03u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc3-sram-32k-v1",     32768u,  32768u,  0u },
    { 0x1Bu, 0x02u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-8k-v1",       8192u,   8192u,  0u },
    { 0x1Bu, 0x03u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-32k-v1",     32768u,  32768u,  0u },
    { 0x1Bu, 0x04u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-128k-v1",   131072u, 131072u,  0u },
    { 0x1Bu, 0x05u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-64k-v1",     65536u,  65536u,  0u },
    { 0x1Eu, 0x02u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-8k-v1",       8192u,   8192u,  0u },
    { 0x1Eu, 0x03u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-32k-v1",     32768u,  32768u,  0u },
    { 0x1Eu, 0x04u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-128k-v1",   131072u, 131072u,  0u },
    { 0x1Eu, 0x05u, HOST_SAVE_FORMAT_ANY_ROM, "gabbaboy-mbc5-sram-64k-v1",     65536u,  65536u,  0u },
};

size_t host_save_format_count(void) { return sizeof(g_rows) / sizeof(g_rows[0]); }

const host_save_format_row *host_save_format_lookup(uint8_t type, uint8_t ram_code, uint8_t rom_code) {
    for (size_t i = 0u; i < sizeof(g_rows) / sizeof(g_rows[0]); ++i) {
        const host_save_format_row *row = &g_rows[i];
        if (row->type == type && row->ram_code == ram_code && rom_code <= row->rom_code_max) return row;
    }
    return NULL;
}
