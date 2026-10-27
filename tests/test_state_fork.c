/* White-box fork tests over the public save/load calls. The included core is
 * used only to poison a receiving instance and record the actual serialized
 * field values at a public save boundary. */
#ifndef GBB_CORE_SOURCE_PATH
#define GBB_CORE_SOURCE_PATH "../src/core/gabbaboy.c"
#endif
#ifdef GBB_STATE_FORK_MUTANT
const char *state_fork_mutant_field;
#endif
#include GBB_CORE_SOURCE_PATH

#include <stdio.h>
#include <stdlib.h>

#define FRAME_PIXELS (GBB_FRAME_WIDTH * GBB_FRAME_HEIGHT)
#define FORK_AUDIO_CAPACITY 2048u
#define GENERATED_APU_ROM_SIZE 0x8000u
#define GENERATED_APU_ROM_PATH "@generated/apu_fields"
#define GENERATED_BUS_ROM_SIZE 0x8000u
#define GENERATED_MBC1_ROM_SIZE 0x200000u
#define GENERATED_MBC3_ROM_SIZE 0x8000u
#define FORK_STATE_HEADER_BYTES 64u

static void set_palette(gbb_compat_palette *palette, uint16_t seed) {
    memset(palette, 0, sizeof(*palette));
    palette->struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    for (size_t i = 0u; i < 4u; ++i) {
        palette->bg[i] = (uint16_t)((seed + i * 0x31u) & 0x7FFFu);
        palette->obj0[i] = (uint16_t)((seed + 0x100u + i * 0x53u) & 0x7FFFu);
        palette->obj1[i] = (uint16_t)((seed + 0x200u + i * 0x71u) & 0x7FFFu);
    }
}

/* Original bounded field-census program. It powers the APU, triggers a
 * negative pulse sweep, and enables noise and wave channels before looping. */
static void finish_generated_rom(uint8_t *rom, size_t size, uint8_t cgb_flag,
                                 uint8_t cartridge_type, uint8_t rom_size,
                                 uint8_t ram_size, const uint8_t *program,
                                 size_t program_size) {
    memset(rom, 0, size);
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    rom[0x143u] = cgb_flag;
    rom[0x147u] = cartridge_type;
    rom[0x148u] = rom_size;
    rom[0x149u] = ram_size;
    memcpy(rom + 0x200u, program, program_size);
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void build_generated_apu_rom(uint8_t rom[GENERATED_APU_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x00u,                    /* Put the first synthesis edge off the sample boundary. */
        0x3Eu, 0x80u, 0xE0u, 0x26u, /* NR52: sound on */
        0x3Eu, 0x77u, 0xE0u, 0x24u, /* NR50: full output level */
        0x3Eu, 0xFFu, 0xE0u, 0x25u, /* NR51: route all channels */
        0x3Eu, 0x19u, 0xE0u, 0x10u, /* NR10: period 1, negate, shift 1 */
        0x3Eu, 0x80u, 0xE0u, 0x11u, /* NR11: pulse duty */
        0x3Eu, 0xF0u, 0xE0u, 0x12u, /* NR12: nonzero pulse envelope */
        0x3Eu, 0x00u, 0xE0u, 0x13u, /* NR13: pulse frequency low */
        0x3Eu, 0x84u, 0xE0u, 0x14u, /* NR14: trigger at frequency 1024 */
        0x3Eu, 0x01u, 0xE0u, 0x20u, /* NR41: non-default noise length */
        0x3Eu, 0xF0u, 0xE0u, 0x21u, /* NR42: nonzero noise envelope */
        0x3Eu, 0xF7u, 0xE0u, 0x22u, /* NR43: divisor 112, shift 15 */
        0x3Eu, 0xC0u, 0xE0u, 0x23u, /* NR44: length enabled and trigger */
        0x3Eu, 0x43u, 0xE0u, 0x1Bu, /* NR31: non-default wave length register */
        0x3Eu, 0x12u, 0xE0u, 0x30u, /* Wave RAM: packed samples before channel enable */
        0x3Eu, 0x34u, 0xE0u, 0x31u,
        0x3Eu, 0x56u, 0xE0u, 0x32u,
        0x3Eu, 0x78u, 0xE0u, 0x33u,
        0x3Eu, 0x9Au, 0xE0u, 0x34u,
        0x3Eu, 0xBCu, 0xE0u, 0x35u,
        0x3Eu, 0xDEu, 0xE0u, 0x36u,
        0x3Eu, 0xF0u, 0xE0u, 0x37u,
        0x3Eu, 0x0Fu, 0xE0u, 0x38u,
        0x3Eu, 0x1Eu, 0xE0u, 0x39u,
        0x3Eu, 0x2Du, 0xE0u, 0x3Au,
        0x3Eu, 0x3Cu, 0xE0u, 0x3Bu,
        0x3Eu, 0x4Bu, 0xE0u, 0x3Cu,
        0x3Eu, 0x5Au, 0xE0u, 0x3Du,
        0x3Eu, 0x69u, 0xE0u, 0x3Eu,
        0x3Eu, 0x78u, 0xE0u, 0x3Fu,
        0x3Eu, 0x80u, 0xE0u, 0x1Au, /* NR30: wave DAC on */
        0x3Eu, 0x20u, 0xE0u, 0x1Cu, /* NR32: wave output level */
        0x3Eu, 0x34u, 0xE0u, 0x1Du, /* NR33: non-default wave frequency low */
        0x3Eu, 0x87u, 0xE0u, 0x1Eu, /* NR34: trigger wave at frequency 1844 */
        0x18u, 0xFEu               /* JR -2 */
    };
    finish_generated_rom(rom, GENERATED_APU_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_bus_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0x80u, 0xE0u, 0x02u, /* Start internal-clock serial transfer. */
        0x3Eu, 0x55u, 0xE0u, 0x01u, /* Writes during transfer latch deferred bus state. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_mbc1_rom(uint8_t rom[GENERATED_MBC1_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0x02u, 0xEAu, 0x00u, 0x40u, /* MBC1 upper ROM bank bits. */
        0x3Eu, 0x01u, 0xEAu, 0x00u, 0x60u, /* MBC1 RAM/ROM banking mode. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_MBC1_ROM_SIZE, 0x80u, 0x01u,
                         0x06u, 0x00u, program, sizeof(program));
}

static void build_generated_mbc3_rtc_rom(uint8_t rom[GENERATED_MBC3_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0x0Au, 0xEAu, 0x00u, 0x00u, /* Enable RTC register writes. */
        0x3Eu, 0x08u, 0xEAu, 0x00u, 0x40u, 0x3Eu, 0x3Bu, 0xEAu, 0x00u, 0xA0u,
        0x3Eu, 0x09u, 0xEAu, 0x00u, 0x40u, 0x3Eu, 0x2Du, 0xEAu, 0x00u, 0xA0u,
        0x3Eu, 0x0Au, 0xEAu, 0x00u, 0x40u, 0x3Eu, 0x13u, 0xEAu, 0x00u, 0xA0u,
        0x3Eu, 0x0Bu, 0xEAu, 0x00u, 0x40u, 0x3Eu, 0xAAu, 0xEAu, 0x00u, 0xA0u,
        0x3Eu, 0x0Cu, 0xEAu, 0x00u, 0x40u, 0x3Eu, 0xC1u, 0xEAu, 0x00u, 0xA0u,
        0x3Eu, 0x00u, 0xEAu, 0x00u, 0x60u, /* RTC latch edge: 0. */
        0x3Eu, 0x01u, 0xEAu, 0x00u, 0x60u, /* RTC latch edge: 1. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_MBC3_ROM_SIZE, 0x80u, 0x10u,
                         0x00u, 0x02u, program, sizeof(program));
}

static void build_generated_stop_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {0x10u, 0x00u, 0x18u, 0xFEu};
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_key1_switch_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0x01u, 0xE0u, 0x4Du, /* Arm CGB speed switch. */
        0x10u, 0x00u,               /* STOP consumes the armed switch. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0xC0u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_lockup_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {0xD3u}; /* Invalid opcode: stable lockup state. */
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_ei_delay_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {0xFBu, 0x00u, 0x18u, 0xFDu};
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_halt_bug_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0x01u, 0xE0u, 0x0Fu, /* Set VBlank IF. */
        0xE0u, 0xFFu,              /* Enable VBlank IE while IME remains clear. */
        0x76u, 0x00u, 0x18u, 0xFDu /* HALT with pending enabled interrupt. */
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_oam_dma_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0xC0u, 0xE0u, 0x46u, /* DMA from initialized work RAM. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_irq_dma_pending_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x31u, 0x47u, 0xFFu,        /* IRQ stack first writes to FF46. */
        0x3Eu, 0x01u, 0xE0u, 0xFFu, /* Enable VBlank. */
        0xE0u, 0x0Fu,                /* Request VBlank. */
        0xFBu, 0x00u,                /* Enable IME after the following NOP. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_timer_reload_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x3Eu, 0x00u, 0xE0u, 0x04u, /* Reset DIV. */
        0x3Eu, 0xFFu, 0xE0u, 0x05u, /* Set TIMA one increment before overflow. */
        0x3Eu, 0x05u, 0xE0u, 0x07u, /* Enable fastest timer tap. */
        0x18u, 0xFEu
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static void build_generated_loop_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE], uint8_t cgb_flag) {
    static const uint8_t program[] = {0x00u, 0x18u, 0xFDu};
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, cgb_flag, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static size_t emit_ldh_write(uint8_t *program, size_t offset,
                             uint8_t address, uint8_t value) {
    program[offset++] = 0x3Eu;
    program[offset++] = value;
    program[offset++] = 0xE0u;
    program[offset++] = address;
    return offset;
}

static size_t emit_absolute_write(uint8_t *program, size_t offset,
                                  uint16_t address, uint8_t value) {
    program[offset++] = 0x3Eu;
    program[offset++] = value;
    program[offset++] = 0xEAu;
    program[offset++] = (uint8_t)address;
    program[offset++] = (uint8_t)(address >> 8);
    return offset;
}

static void build_generated_native_pipeline_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    uint8_t program[256];
    size_t length = 0u;
    length = emit_ldh_write(program, length, 0x40u, 0x00u); /* LCD off for OAM initialization. */
    length = emit_absolute_write(program, length, 0xFE00u, 0u); /* Keep entry zero off-screen. */
    length = emit_absolute_write(program, length, 0xFE01u, 0u);
    length = emit_absolute_write(program, length, 0xFE02u, 0u);
    length = emit_absolute_write(program, length, 0xFE03u, 0u);
    length = emit_absolute_write(program, length, 0xFE04u, 16u); /* Visible entry one. */
    length = emit_absolute_write(program, length, 0xFE05u, 16u);
    length = emit_absolute_write(program, length, 0xFE06u, 1u);
    length = emit_absolute_write(program, length, 0xFE07u, 0x20u);
    length = emit_ldh_write(program, length, 0x43u, 3u); /* Fine-scroll discard. */
    length = emit_ldh_write(program, length, 0x4Au, 0u); /* Window starts on line zero. */
    length = emit_ldh_write(program, length, 0x4Bu, 7u); /* Window begins at x zero. */
    length = emit_ldh_write(program, length, 0x56u, 0xC1u); /* RP receiver enabled. */
    length = emit_ldh_write(program, length, 0x74u, 0x55u); /* Native-only CGB register. */
    length = emit_ldh_write(program, length, 0x4Du, 1u); /* Keep KEY1 armed at the save boundary. */
    length = emit_ldh_write(program, length, 0x70u, 3u); /* WRAM bank three. */
    length = emit_ldh_write(program, length, 0x6Cu, 1u); /* OPRI bit zero. */
    length = emit_ldh_write(program, length, 0x4Fu, 1u); /* Native VRAM bank one. */
    length = emit_ldh_write(program, length, 0x51u, 0xC0u); /* HDMA source: WRAM. */
    length = emit_ldh_write(program, length, 0x52u, 0x20u);
    length = emit_ldh_write(program, length, 0x53u, 0x01u); /* HDMA destination high bits. */
    length = emit_ldh_write(program, length, 0x54u, 0x40u);
    length = emit_ldh_write(program, length, 0x40u, 0xB3u); /* LCD/window/OBJ enabled. */
    length = emit_ldh_write(program, length, 0x55u, 0x81u); /* Two HBlank blocks. */
    program[length++] = 0x18u;
    program[length++] = 0xFEu;
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0xC0u, 0x00u,
                         0x00u, 0x00u, program, length);
}

static void build_generated_dmg_pipeline_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    uint8_t program[96];
    size_t length = 0u;
    length = emit_ldh_write(program, length, 0x40u, 0x00u); /* Initialize OAM with LCD off. */
    length = emit_absolute_write(program, length, 0xFE00u, 16u);
    length = emit_absolute_write(program, length, 0xFE01u, 16u);
    length = emit_absolute_write(program, length, 0xFE02u, 1u);
    length = emit_absolute_write(program, length, 0xFE03u, 0u);
    length = emit_ldh_write(program, length, 0x43u, 3u); /* Fine-scroll discard. */
    length = emit_ldh_write(program, length, 0x4Au, 0u); /* Window starts on line zero. */
    length = emit_ldh_write(program, length, 0x4Bu, 7u); /* Window begins at x zero. */
    length = emit_ldh_write(program, length, 0x40u, 0xB3u); /* LCD/window/OBJ enabled. */
    program[length++] = 0x18u;
    program[length++] = 0xFEu;
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x00u, 0x00u,
                         0x00u, 0x00u, program, length);
}

static void build_generated_div_read_rom(uint8_t rom[GENERATED_BUS_ROM_SIZE]) {
    static const uint8_t program[] = {
        0x21u, 0x00u, 0xC0u, /* HL = work RAM destination. */
        0x00u,               /* Save immediately before the DIV read. */
        0xF0u, 0x04u,        /* LDH A,(DIV). */
        0x22u,               /* Store the observed value and advance HL. */
        0x18u, 0xF7u          /* Repeat, preserving the first observation at C000. */
    };
    finish_generated_rom(rom, GENERATED_BUS_ROM_SIZE, 0x80u, 0x00u,
                         0x00u, 0x00u, program, sizeof(program));
}

static int generated_rom(const char *id, uint8_t **out, size_t *size) {
    *out = NULL;
    *size = 0u;
    if (strcmp(id, "apu_fields") == 0) *size = GENERATED_APU_ROM_SIZE;
    else if (strcmp(id, "bus_unsupported") == 0) *size = GENERATED_BUS_ROM_SIZE;
    else if (strcmp(id, "mbc1_fields") == 0) *size = GENERATED_MBC1_ROM_SIZE;
    else if (strcmp(id, "mbc3_rtc_fields") == 0) *size = GENERATED_MBC3_ROM_SIZE;
    else if (strcmp(id, "stop_wake") == 0 || strcmp(id, "lockup") == 0 ||
             strcmp(id, "key1_switch") == 0 ||
             strcmp(id, "ei_delay") == 0 || strcmp(id, "halt_bug") == 0 ||
             strcmp(id, "oam_dma") == 0 || strcmp(id, "timer_reload") == 0 ||
             strcmp(id, "accepted_flags") == 0 || strcmp(id, "accepted_dma_phase") == 0 ||
             strcmp(id, "joypad_applied") == 0)
        *size = GENERATED_BUS_ROM_SIZE;
    else if (strcmp(id, "irq_dma_pending") == 0) *size = GENERATED_BUS_ROM_SIZE;
    else if (strcmp(id, "native_pipeline") == 0 ||
             strcmp(id, "native_pipeline_hdma") == 0 ||
             strcmp(id, "native_pipeline_pending") == 0 ||
             strcmp(id, "native_pipeline_scroll") == 0 ||
             strcmp(id, "native_pipeline_stall") == 0 ||
             strcmp(id, "native_pipeline_fetch") == 0 ||
             strcmp(id, "dmg_ppu_pipeline") == 0) *size = GENERATED_BUS_ROM_SIZE;
    else if (strcmp(id, "div_read") == 0) *size = GENERATED_BUS_ROM_SIZE;
    else return 0;
    uint8_t *rom = (uint8_t *)malloc(*size);
    if (rom == NULL) return 0;
    if (strcmp(id, "apu_fields") == 0) build_generated_apu_rom(rom);
    else if (strcmp(id, "bus_unsupported") == 0) build_generated_bus_rom(rom);
    else if (strcmp(id, "mbc1_fields") == 0) build_generated_mbc1_rom(rom);
    else if (strcmp(id, "mbc3_rtc_fields") == 0) build_generated_mbc3_rtc_rom(rom);
    else if (strcmp(id, "stop_wake") == 0) build_generated_stop_rom(rom);
    else if (strcmp(id, "key1_switch") == 0) build_generated_key1_switch_rom(rom);
    else if (strcmp(id, "lockup") == 0) build_generated_lockup_rom(rom);
    else if (strcmp(id, "ei_delay") == 0) build_generated_ei_delay_rom(rom);
    else if (strcmp(id, "halt_bug") == 0) build_generated_halt_bug_rom(rom);
    else if (strcmp(id, "oam_dma") == 0) build_generated_oam_dma_rom(rom);
    else if (strcmp(id, "timer_reload") == 0) build_generated_timer_reload_rom(rom);
    else if (strcmp(id, "accepted_dma_phase") == 0) build_generated_oam_dma_rom(rom);
    else if (strcmp(id, "accepted_flags") == 0) build_generated_loop_rom(rom, 0xC0u);
    else if (strcmp(id, "joypad_applied") == 0) build_generated_loop_rom(rom, 0x80u);
    else if (strcmp(id, "dmg_ppu_pipeline") == 0) build_generated_dmg_pipeline_rom(rom);
    else if (strcmp(id, "div_read") == 0) build_generated_div_read_rom(rom);
    else if (strcmp(id, "irq_dma_pending") == 0) build_generated_irq_dma_pending_rom(rom);
    else build_generated_native_pipeline_rom(rom);
    *out = rom;
    return 1;
}

typedef struct {
    const char *path;
    uint64_t value;
} fork_state_seed;

static int load_seeded_public_state(gbb_instance *instance,
                                    const fork_state_seed *seeds,
                                    size_t seed_count) {
    size_t state_size = 0u;
    if (gbb_state_size(instance, &state_size) != GBB_OK) return 0;
    uint8_t *bytes = (uint8_t *)malloc(state_size);
    if (bytes == NULL) return 0;
    if (gbb_save_state(instance, bytes, state_size) != GBB_OK) {
        free(bytes);
        return 0;
    }
    for (size_t i = 0u; i < seed_count; ++i) {
        const state_field_descriptor *field = state_field_by_path(seeds[i].path);
        if (field == NULL || field->wire_width > 8u ||
            state_field_count_for_instance(instance, field) != 1u) {
            free(bytes);
            return 0;
        }
        const size_t offset = state_body_field_offset(instance, field);
        if (offset == SIZE_MAX || offset > state_size - FORK_STATE_HEADER_BYTES ||
            field->wire_width > state_size - FORK_STATE_HEADER_BYTES - offset) {
            free(bytes);
            return 0;
        }
        state_put_u64(bytes + FORK_STATE_HEADER_BYTES + offset,
                      seeds[i].value, field->wire_width);
    }
    uint32_t crc = state_crc32_update(UINT32_MAX, bytes, 60u);
    crc = state_crc32_update(crc, bytes + FORK_STATE_HEADER_BYTES,
        state_size - FORK_STATE_HEADER_BYTES) ^ UINT32_MAX;
    state_put_u32(bytes + 60u, crc);
#ifdef GBB_STATE_FORK_MUTANT
    const char *selected_mutant = state_fork_mutant_field;
    state_fork_mutant_field = NULL;
#endif
    const gbb_error loaded = gbb_load_state(instance, bytes, state_size);
#ifdef GBB_STATE_FORK_MUTANT
    state_fork_mutant_field = selected_mutant;
#endif
    free(bytes);
    return loaded == GBB_OK;
}

static int seed_generated_boundary(const char *case_id, gbb_instance *source) {
    const char *generated_id = strncmp(case_id, "generated:", 10u) == 0
        ? case_id + 10u : "";
    const char *profile_separator = strchr(generated_id, ':');
    const size_t generated_id_size = profile_separator == NULL
        ? strlen(generated_id) : (size_t)(profile_separator - generated_id);
#define GENERATED_IS(ID) (generated_id_size == sizeof(ID) - 1u && \
    memcmp(generated_id, ID, sizeof(ID) - 1u) == 0)
    static const fork_state_seed accepted_flags[] = {
        {"bus_unsupported", 1u}, {"bus_unsupported_address", 0xFF02u},
        {"stop_switch_pending", 1u}, {"divider_phase", 1u},
        {"ppu_half_phase", 1u}
    };
    static const fork_state_seed accepted_timer[] = {
        {"tima", 0u}, {"tma", 0xA5u},
        {"timer_reload_pending", 1u}, {"timer_reload_remaining", 4u}
    };
    static const fork_state_seed accepted_dma[] = {{"dma_phase", 1u}};
    static const fork_state_seed accepted_hdma_pending[] = {{"hdma.pending_hblank", 1u}};
    static const fork_state_seed div_read[] = {{"div", 0xACu}, {"divider_counter", 0xAC00u}};
    const fork_state_seed *seeds = NULL;
    size_t seed_count = 0u;
    if (GENERATED_IS("accepted_flags")) {
        seeds = accepted_flags;
        seed_count = sizeof(accepted_flags) / sizeof(accepted_flags[0]);
    } else if (GENERATED_IS("timer_reload")) {
        seeds = accepted_timer;
        seed_count = sizeof(accepted_timer) / sizeof(accepted_timer[0]);
    } else if (GENERATED_IS("accepted_dma_phase")) {
        seeds = accepted_dma;
        seed_count = sizeof(accepted_dma) / sizeof(accepted_dma[0]);
    } else if (GENERATED_IS("native_pipeline_pending")) {
        seeds = accepted_hdma_pending;
        seed_count = sizeof(accepted_hdma_pending) / sizeof(accepted_hdma_pending[0]);
    } else if (GENERATED_IS("div_read")) {
        seeds = div_read;
        seed_count = sizeof(div_read) / sizeof(div_read[0]);
    }
    if (seed_count == 0u) return 1;
    if (!load_seeded_public_state(source, seeds, seed_count)) {
        fprintf(stderr, "state-fork setup failure: accepted public-state seed refused: %s\n", case_id);
        return 0;
    }
    printf("public-state-seed case=%s origin=crc-valid-public-load fields=", case_id);
    for (size_t i = 0u; i < seed_count; ++i)
        printf("%s%s", i == 0u ? "" : ",", seeds[i].path);
    putchar('\n');
#undef GENERATED_IS
    return 1;
}

static int verify_generated_boundary_predicates(const char *case_id,
                                                const gbb_instance *source,
                                                gbb_run_result prefix) {
    if (strncmp(case_id, "generated:div_read:",
                sizeof("generated:div_read:") - 1u) == 0) {
        const uint16_t hl_value = (uint16_t)(((uint16_t)source->h << 8) | source->l);
        const int passed = source->pc == 0x0204u && hl_value == 0xC000u &&
            prefix.reason == GBB_STOP_BUDGET && prefix.consumed_half_dots == 64u;
        if (!passed) {
            fprintf(stderr, "state-fork boundary predicate failed: %s pc=%04x hl=%04x reason=%d consumed=%llu\n",
                case_id, (unsigned)source->pc, (unsigned)hl_value, (int)prefix.reason,
                (unsigned long long)prefix.consumed_half_dots);
            return 0;
        }
        printf("boundary-predicate case=%s id=pc value=%u context=next-instruction-reads-DIV-and-stores-to-work-RAM\n",
            case_id, (unsigned)source->pc);
        printf("boundary-predicate case=%s id=hl value=%u context=work-RAM-observation-destination\n",
            case_id, (unsigned)hl_value);
    } else if (strncmp(case_id, "generated:key1_switch:",
                sizeof("generated:key1_switch:") - 1u) == 0) {
        const int passed = source->double_speed == 1u &&
            source->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
            source->cpu_stall_half_dots > 0u && source->stop_switch_pending == 0u;
        if (!passed) {
            fprintf(stderr, "state-fork boundary predicate failed: %s double_speed=%u stall=%u remaining=%u stop_switch_pending=%u\n",
                case_id, (unsigned)source->double_speed, (unsigned)source->cpu_stall_kind,
                (unsigned)source->cpu_stall_half_dots, (unsigned)source->stop_switch_pending);
            return 0;
        }
        printf("boundary-predicate case=%s id=stop_switch_pending value=0 context=speed-switch-stall\n",
               case_id);
    } else if (strncmp(case_id, "generated:bus_unsupported:",
                       sizeof("generated:bus_unsupported:") - 1u) == 0) {
        const int passed = prefix.reason == GBB_STOP_UNSUPPORTED_BUS &&
            source->bus_unsupported == 0 && source->bus_unsupported_address == 0xFF01u;
        if (!passed) {
            fprintf(stderr, "state-fork boundary predicate failed: %s reason=%d bus_unsupported=%d address=%04x\n",
                case_id, (int)prefix.reason, source->bus_unsupported,
                (unsigned)source->bus_unsupported_address);
            return 0;
        }
        printf("boundary-predicate case=%s id=bus_unsupported value=0 context=unsupported-bus-return\n",
               case_id);
    }
    return 1;
}

static void generated_rom_sha256(const uint8_t *rom, size_t size, char out[65]) {
    static const char hex[] = "0123456789abcdef";
    uint8_t digest[32];
    state_sha256(rom, size, digest);
    for (size_t i = 0u; i < sizeof(digest); ++i) {
        out[i * 2u] = hex[digest[i] >> 4];
        out[i * 2u + 1u] = hex[digest[i] & 0x0Fu];
    }
    out[64] = '\0';
}

static int read_file(const char *path, uint8_t **out_bytes, size_t *out_size) {
    *out_bytes = NULL;
    *out_size = 0u;
    if (strncmp(path, "@generated/", 11u) == 0) {
        return generated_rom(path + 11u, out_bytes, out_size);
    }
    FILE *file = fopen(path, "rb");
    if (file == NULL || fseek(file, 0, SEEK_END) != 0) {
        if (file != NULL) fclose(file);
        return 0;
    }
    const long end = ftell(file);
    if (end <= 0 || (uintmax_t)end > SIZE_MAX || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 0;
    }
    uint8_t *bytes = (uint8_t *)malloc((size_t)end);
    if (bytes == NULL) {
        fclose(file);
        return 0;
    }
    const size_t got = fread(bytes, 1u, (size_t)end, file);
    const int close_ok = fclose(file) == 0;
    if (got != (size_t)end || !close_ok) {
        free(bytes);
        return 0;
    }
    *out_bytes = bytes;
    *out_size = (size_t)end;
    return 1;
}

static int load_instance(const char *rom_path, gbb_profile profile,
                         gbb_instance **out_instance) {
    uint8_t *rom = NULL;
    size_t rom_size = 0u;
    *out_instance = NULL;
    if (!read_file(rom_path, &rom, &rom_size)) return 0;
    const gbb_error created = gbb_create(profile, out_instance);
    const gbb_error loaded = created == GBB_OK
        ? gbb_load_rom(*out_instance, rom, rom_size) : created;
    free(rom);
    if (loaded != GBB_OK) {
        gbb_destroy(*out_instance);
        *out_instance = NULL;
        return 0;
    }
    return 1;
}

static int same_run(gbb_run_result a, gbb_run_result b) {
    return a.consumed_half_dots == b.consumed_half_dots && a.reason == b.reason &&
           a.trace_count == b.trace_count && a.diagnostic_count == b.diagnostic_count &&
           a.lockup_pc == b.lockup_pc && a.lockup_opcode == b.lockup_opcode;
}

static int copy_frame_equal(const gbb_instance *a, const gbb_instance *b,
                            gbb_profile profile) {
    if (profile == GBB_PROFILE_DMG_CPU_B) {
        uint8_t left[FRAME_PIXELS], right[FRAME_PIXELS];
        gbb_frame_info left_info = {0}, right_info = {0};
        const gbb_error left_status = gbb_copy_frame(a, left, sizeof(left),
            GBB_FRAME_WIDTH, &left_info);
        const gbb_error right_status = gbb_copy_frame(b, right, sizeof(right),
            GBB_FRAME_WIDTH, &right_info);
        return left_status == right_status && left_status == GBB_FRAME_NOT_READY
            ? 1 : left_status == GBB_OK && right_status == GBB_OK &&
                memcmp(left, right, sizeof(left)) == 0 &&
                memcmp(&left_info, &right_info, sizeof(left_info)) == 0;
    }
    uint16_t left[FRAME_PIXELS], right[FRAME_PIXELS];
    gbb_frame_info left_info = {0}, right_info = {0};
    const size_t bytes = sizeof(left);
    const gbb_error left_status = gbb_copy_frame_rgb555(a, left, bytes,
        GBB_FRAME_WIDTH * sizeof(uint16_t), &left_info);
    const gbb_error right_status = gbb_copy_frame_rgb555(b, right, bytes,
        GBB_FRAME_WIDTH * sizeof(uint16_t), &right_info);
    return left_status == right_status && left_status == GBB_FRAME_NOT_READY
        ? 1 : left_status == GBB_OK && right_status == GBB_OK &&
            memcmp(left, right, bytes) == 0 &&
            memcmp(&left_info, &right_info, sizeof(left_info)) == 0;
}

static int copy_battery(const gbb_instance *instance, uint8_t **out_bytes,
                        size_t *out_size, gbb_error *out_status) {
    *out_bytes = NULL;
    *out_size = 0u;
    *out_status = gbb_battery_size(instance, out_size);
    if (*out_status != GBB_OK) return 1;
    *out_bytes = (uint8_t *)malloc(*out_size == 0u ? 1u : *out_size);
    if (*out_bytes == NULL) return 0;
    *out_status = gbb_copy_battery(instance, *out_bytes, *out_size);
    return *out_status == GBB_OK;
}

static int copy_rumble(const gbb_instance *instance, gbb_error *out_status,
                       uint8_t *out_level, uint64_t *out_changes) {
    *out_level = 0u;
    *out_changes = 0u;
    *out_status = gbb_rumble_state(instance, out_level, out_changes);
    return *out_status == GBB_OK || *out_status == GBB_NO_RUMBLE;
}

static uint64_t observer_delta(uint64_t before, uint64_t after) {
    return after >= before ? after - before : UINT64_MAX - before + after + 1u;
}

static uint64_t poison_value(const state_field_descriptor *field, uint64_t value) {
    if (field->kind == STATE_VALUE_BOOL) return value == 0u ? 1u : 0u;
    if (field->kind == STATE_VALUE_EVENT_KIND) return value == 0u ? 1u : 0u;
    if (strcmp(field->path, "time_half_dots") == 0 ||
        strcmp(field->path, "instruction_start_half_dots") == 0 ||
        strcmp(field->path, "cart.rtc_synced_at") == 0) return 0u;
    if (strcmp(field->path, "cart.rtc_sub") == 0) return value == 1u ? 2u : 1u;
    if (strcmp(field->path, "compat_rgb555") == 0) return (value ^ UINT64_C(0x1111)) & 0x7FFFu;
    switch (field->wire_width) {
    case 1u: return (value ^ UINT64_C(0x5A)) & UINT64_C(0xFF);
    case 2u: return (value ^ UINT64_C(0x1555)) & UINT64_C(0x7FFF);
    case 4u: return value ^ UINT64_C(0x55555555);
    case 8u: return value ^ UINT64_C(0x5555555555555555);
    default: return value == 0u ? 1u : 0u;
    }
}

static int poison_serialized_storage(gbb_instance *target,
                                     const gbb_instance *source) {
    const size_t fields = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    for (size_t f = 0u; f < fields; ++f) {
        state_field_record record = {0};
        if (!state_record_field(source, f, &record) ||
            record.width != STATE_FIELDS[f].wire_width) {
            fprintf(stderr, "state-fork poison descriptor failure: index=%zu\n", f);
            return 0;
        }
        if (record.count == 0u) continue;
        for (size_t i = 0u; i < record.count; ++i) {
            uint64_t actual = 0u;
            const int read_ok = state_host_value(source, &STATE_FIELDS[f], i, &actual);
            const int store_ok = read_ok && state_store_host_value(target,
                &STATE_FIELDS[f], i, poison_value(&STATE_FIELDS[f], actual));
            if (!read_ok || !store_ok) {
                fprintf(stderr, "state-fork poison failure: id=%s index=%zu raw=%016llx\n",
                    record.qualified_id, i, (unsigned long long)actual);
                return 0;
            }
        }
    }
    return 1;
}

static int emit_field_witnesses(const char *case_id, const gbb_instance *source,
                                const gbb_instance *baseline) {
    const size_t fields = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    for (size_t f = 0u; f < fields; ++f) {
        state_field_record record = {0};
        if (!state_record_field(source, f, &record)) return 0;
        for (size_t i = 0u; i < record.count; ++i) {
            uint64_t raw = 0u, default_raw = 0u;
            if (!state_host_value(source, &STATE_FIELDS[f], i, &raw) ||
                !state_host_value(baseline, &STATE_FIELDS[f], i, &default_raw)) return 0;
            if (raw != default_raw) {
                printf("field-witness case=%s id=%s offset=%zu count=%zu width=%u index=%zu value=%016llx default=%016llx discriminator=nondefault treatment=serialize\n",
                    case_id, record.qualified_id, record.offset, record.count,
                    (unsigned)record.width, i, (unsigned long long)raw,
                    (unsigned long long)default_raw);
                break;
            }
        }
    }
    return 1;
}

static void emit_inflight_categories(const char *case_id, const gbb_instance *m) {
#define CATEGORY_IF(ID, CONDITION) do { if (CONDITION) \
    printf("category-witness case=%s id=%s model=%s mode=%u\n", case_id, ID, \
        m->profile == GBB_PROFILE_CGB_CPU_E ? "CGB" : "DMG", (unsigned)m->exec_mode); \
} while (0)
    CATEGORY_IF("oam_dma", m->dma_active && m->dma_index > 0u && m->dma_index < 160u);
    CATEGORY_IF("hdma_byte_phase", m->hdma.active && m->hdma.byte_phase > 0u);
    CATEGORY_IF("speed_switch_stall", m->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
                m->cpu_stall_half_dots > 0u);
    CATEGORY_IF("halt", m->halted);
    CATEGORY_IF("ei_delay", m->ime_delay == 1u);
    CATEGORY_IF("apu_sequencer", m->apu_sequencer_step != 0u);
    CATEGORY_IF("rtc_subsecond", m->cart.has_timer && m->cart.rtc_sub != 0u);
    CATEGORY_IF("partial_frame", m->ppu_dot != 0u || m->ppu_fifo_count != 0u);
    CATEGORY_IF("timer_reload", m->timer_reload_pending && m->timer_reload_remaining > 0u);
    CATEGORY_IF("serial", m->serial_active && m->serial_bits < 8u);
    CATEGORY_IF("queued_input", m->input_event_count > 0u);
    CATEGORY_IF("queued_wake", m->stopped && m->input_event_count > 0u);
    CATEGORY_IF("ppu_fifo_window", m->ppu_fifo_count > 0u && m->ppu_window_started);
    CATEGORY_IF("lockup", m->locked && m->lockup_pc == m->pc);
#undef CATEGORY_IF
}

static int state_fork_case(const char *case_id, const char *rom_path,
                           gbb_profile profile, uint64_t prefix_budget) {
    gbb_instance *source = NULL, *target = NULL, *baseline = NULL;
    if (!load_instance(rom_path, profile, &source) ||
        !load_instance(rom_path, profile, &target) ||
        !load_instance(rom_path, profile, &baseline)) {
        gbb_destroy(baseline);
        gbb_destroy(target);
        gbb_destroy(source);
        fprintf(stderr, "state-fork setup failure: %s\n", case_id);
        return 2;
    }
    gbb_audio_frame prefix_audio[FORK_AUDIO_CAPACITY];
    size_t prefix_count = 0u;
    const gbb_run_result prefix = gbb_run_audio(source, prefix_budget,
        prefix_audio, FORK_AUDIO_CAPACITY, &prefix_count);
    if (strncmp(case_id, "generated:", 10u) == 0)
        printf("seed-boundary case=%s requested=%llu consumed=%llu reason=%d time=%llu\n",
            case_id, (unsigned long long)prefix_budget,
            (unsigned long long)prefix.consumed_half_dots, (int)prefix.reason,
            (unsigned long long)source->time_half_dots);
    if (prefix.reason == GBB_STOP_INVALID_STATE || prefix.reason == GBB_STOP_NO_PROGRESS) {
        fprintf(stderr, "state-fork setup failure: public prefix did not advance: %s\n", case_id);
        gbb_destroy(target);
        gbb_destroy(baseline);
        gbb_destroy(source);
        return 2;
    }
    const uint64_t source_battery_before = source->battery_generation;
    const uint64_t source_rumble_before = source->cart.rumble_changes;

    /* Create receiving-side observer and guest history, then restore the exact
     * source palette and serialized state through the public loader. */
    const gbb_run_result ahead = gbb_run(target, UINT64_C(71321), NULL, 0u);
    if (ahead.reason == GBB_STOP_INVALID_STATE) {
        fprintf(stderr, "state-fork setup failure: target prefix invalid: %s\n", case_id);
        gbb_destroy(target);
        gbb_destroy(source);
        return 2;
    }
    if (profile == GBB_PROFILE_CGB_CPU_E) {
        gbb_compat_palette source_palette, target_palette;
        set_palette(&source_palette, 0x013u);
        set_palette(&target_palette, 0x713u);
        if (gbb_set_compat_palette(source, &source_palette) != GBB_OK ||
            gbb_set_compat_palette(target, &target_palette) != GBB_OK) {
            fprintf(stderr, "state-fork setup failure: palette setup: %s\n", case_id);
            gbb_destroy(target);
            gbb_destroy(source);
            return 2;
        }
    }
    gbb_input_event queued = {0};
    const int immediate_button = strncmp(case_id, "generated:joypad_applied:",
        sizeof("generated:joypad_applied:") - 1u) == 0;
    const int stop_wake = strncmp(case_id, "generated:stop_wake:",
        sizeof("generated:stop_wake:") - 1u) == 0;
    queued.at_half_dots = source->time_half_dots +
        (immediate_button ? 1u : UINT64_C(70000));
    queued.kind = stop_wake ? GBB_INPUT_STOP_WAKE : GBB_INPUT_BUTTON_PRESS;
    queued.value = stop_wake ? 1u : GBB_BUTTON_A;
    if (gbb_queue_events(source, &queued, 1u) != GBB_OK) {
        fprintf(stderr, "state-fork setup failure: queued input: %s\n", case_id);
        gbb_destroy(target);
        gbb_destroy(baseline);
        gbb_destroy(source);
        return 2;
    }
    if (immediate_button) {
        const gbb_run_result input_run = gbb_run(source, 8u, NULL, 0u);
        if (input_run.consumed_half_dots == 0u ||
            (source->joypad_buttons & (1u << GBB_BUTTON_A)) == 0u) {
            fprintf(stderr, "state-fork setup failure: applied joypad event not observed: %s\n", case_id);
            gbb_destroy(target);
            gbb_destroy(baseline);
            gbb_destroy(source);
            return 2;
        }
    }
    if (!seed_generated_boundary(case_id, source)) {
        gbb_destroy(target);
        gbb_destroy(baseline);
        gbb_destroy(source);
        return 2;
    }
    if (!verify_generated_boundary_predicates(case_id, source, prefix)) {
        gbb_destroy(target);
        gbb_destroy(baseline);
        gbb_destroy(source);
        return 2;
    }

    size_t state_size = 0u;
    const gbb_error sized = gbb_state_size(source, &state_size);
    if (sized != GBB_OK) {
        fprintf(stderr, "state-fork setup failure: state size: %s error=%d time=%llu prefix_reason=%d fields_valid=%d relations_valid=%d profile=%u mode=%u double_speed=%u stall=%u stall_ticks=%u key1=%u stop_pending=%u events=%u pulse0_frequency=%u pulse0_timer=%u\n",
                case_id, (int)sized, (unsigned long long)source->time_half_dots,
                (int)prefix.reason, state_validate_fields(source, NULL, 0u),
                state_validate_relations(source, NULL, 0u), (unsigned)source->profile,
                (unsigned)source->exec_mode, (unsigned)source->double_speed,
                (unsigned)source->cpu_stall_kind, (unsigned)source->cpu_stall_half_dots,
                (unsigned)source->key1_armed, (unsigned)source->stop_switch_pending,
                (unsigned)source->input_event_count,
                (unsigned)source->apu_pulse[0].frequency,
                (unsigned)source->apu_pulse[0].timer);
        uint64_t phase = source->apu_sample_phase;
        for (size_t f = 0u; f < sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]); ++f) {
            const state_field_descriptor *field = &STATE_FIELDS[f];
            const size_t count = state_field_count_for_instance(source, field);
            for (size_t i = 0u; i < count; ++i) {
                uint64_t raw = 0u;
                if (!state_host_value(source, field, i, &raw) ||
                    !state_field_value_valid(source, field, i, raw,
                        source->audio_event_head, phase))
                    fprintf(stderr, "state-fork invalid-live-field id=%s index=%zu raw=%016llx\n",
                        field->path, i, (unsigned long long)raw);
            }
        }
        gbb_destroy(target);
        gbb_destroy(baseline);
        gbb_destroy(source);
        return 2;
    }
    uint8_t *saved = (uint8_t *)malloc(state_size);
    uint8_t *source_final = (uint8_t *)malloc(state_size);
    uint8_t *target_final = (uint8_t *)malloc(state_size);
    const gbb_error save_status = saved == NULL ? GBB_OUT_OF_MEMORY
        : gbb_save_state(source, saved, state_size);
    const int witness_status = save_status == GBB_OK
        ? emit_field_witnesses(case_id, source, baseline) : 0;
    emit_inflight_categories(case_id, source);
    if (saved == NULL || source_final == NULL || target_final == NULL ||
        save_status != GBB_OK || !witness_status) {
        fprintf(stderr, "state-fork setup failure: save/witness: %s save=%d witness=%d\n",
                case_id, (int)save_status, witness_status);
        free(target_final); free(source_final); free(saved);
        gbb_destroy(target); gbb_destroy(source);
        gbb_destroy(baseline);
        return 2;
    }

    uint8_t *old_battery = NULL;
    size_t old_battery_size = 0u;
    gbb_error old_battery_status = GBB_OK;
    gbb_error old_rumble_status = GBB_OK;
    uint8_t old_rumble_level = 0u;
    uint64_t old_rumble_changes = 0u;
    target->battery_generation = 11u;
    target->cart.rumble_changes = 17u;
    if (!poison_serialized_storage(target, source)) {
        fprintf(stderr, "state-fork setup failure: poison: %s\n", case_id);
        free(target_final); free(source_final); free(saved);
        gbb_destroy(target); gbb_destroy(source);
        gbb_destroy(baseline);
        return 2;
    }
    const uint8_t old_rumble_raw = target->cart.rumble_on;
    if (!copy_battery(target, &old_battery, &old_battery_size, &old_battery_status) ||
        !copy_rumble(target, &old_rumble_status, &old_rumble_level,
                     &old_rumble_changes)) {
        fprintf(stderr, "state-fork setup failure: pre-load observer projection: %s\n", case_id);
        free(old_battery); free(target_final); free(source_final); free(saved);
        gbb_destroy(target); gbb_destroy(source);
        gbb_destroy(baseline);
        return 2;
    }
    const gbb_error loaded = gbb_load_state(target, saved, state_size);
    if (loaded != GBB_OK) {
        fprintf(stderr, "state-fork load failure: %s error=%d\n", case_id, (int)loaded);
        free(old_battery); free(target_final); free(source_final); free(saved);
        gbb_destroy(target); gbb_destroy(source);
        gbb_destroy(baseline);
        return 1;
    }
#ifdef GBB_STATE_FORK_MUTANT
    if (state_fork_mutant_field != NULL) {
        const state_field_descriptor *mutated =
            state_field_by_path(state_fork_mutant_field);
        int omission_observed = 0;
        if (mutated != NULL) {
            const size_t count = state_field_count_for_instance(source, mutated);
            for (size_t i = 0u; i < count; ++i) {
                uint64_t expected = 0u, actual = 0u;
                if (!state_host_value(source, mutated, i, &expected) ||
                    !state_host_value(target, mutated, i, &actual)) break;
                if (expected != actual) omission_observed = 1;
            }
        }
        if (!omission_observed) {
            fprintf(stderr, "state-fork setup failure: field omission did not preserve poison: %s\n",
                state_fork_mutant_field);
            free(old_battery); free(target_final); free(source_final); free(saved);
            gbb_destroy(target); gbb_destroy(source); gbb_destroy(baseline);
            return 2;
        }
        printf("state-fork mutation-applied field=%s case=%s\n", state_fork_mutant_field, case_id);
    }
#endif
    const gbb_error post_load_save_status =
        gbb_save_state(target, target_final, state_size);
    const int post_load_canonical_equal = post_load_save_status == GBB_OK &&
        memcmp(saved, target_final, state_size) == 0;
    if (!post_load_canonical_equal)
        fprintf(stderr, "state-fork discrepancy case=%s observation=post-load-canonical-state-bytes-or-save-status\n",
            case_id);

    uint8_t *new_battery = NULL;
    size_t new_battery_size = 0u;
    gbb_error new_battery_status = GBB_OK;
    gbb_error new_rumble_status = GBB_OK;
    uint8_t new_rumble_level = 0u;
    uint64_t new_rumble_changes = 0u;
    if (!copy_battery(target, &new_battery, &new_battery_size, &new_battery_status) ||
        !copy_rumble(target, &new_rumble_status, &new_rumble_level,
                     &new_rumble_changes)) {
        fprintf(stderr, "state-fork observer failure: %s\n", case_id);
        free(new_battery); free(old_battery); free(target_final); free(source_final); free(saved);
        gbb_destroy(target); gbb_destroy(source);
        gbb_destroy(baseline);
        return 1;
    }
    const int battery_changed = old_battery_status != new_battery_status ||
        old_battery_size != new_battery_size ||
        (old_battery_size != 0u && memcmp(old_battery, new_battery, old_battery_size) != 0);
    const uint64_t expected_battery_generation = 11u + (battery_changed ? 1u : 0u);
    const uint64_t expected_rumble_changes = 17u +
        (old_rumble_raw != source->cart.rumble_on ? 1u : 0u);
    if (target->battery_generation != expected_battery_generation)
        fprintf(stderr, "state-fork discrepancy case=%s observation=battery-observer-counter\n", case_id);
    if (target->cart.rumble_changes != expected_rumble_changes)
        fprintf(stderr, "state-fork discrepancy case=%s observation=rumble-observer-counter\n", case_id);
    if (target->battery_generation != expected_battery_generation ||
        target->cart.rumble_changes != expected_rumble_changes) {
        fprintf(stderr, "state-fork mismatch: observer-delta case=%s battery=%llu expected=%llu rumble=%llu expected=%llu\n",
            case_id, (unsigned long long)target->battery_generation,
            (unsigned long long)expected_battery_generation,
            (unsigned long long)target->cart.rumble_changes,
            (unsigned long long)expected_rumble_changes);
        free(new_battery); free(old_battery); free(target_final); free(source_final); free(saved);
        gbb_destroy(target); gbb_destroy(source);
        return 1;
    }
    const uint64_t source_battery_base = source->battery_generation;
    const uint64_t target_battery_base = target->battery_generation;
    const uint64_t source_rumble_base = source->cart.rumble_changes;
    const uint64_t target_rumble_base = target->cart.rumble_changes;
    (void)source_battery_before;
    (void)source_rumble_before;

    int equal = 1;
    const uint64_t future_budgets[] = {UINT64_C(70117), UINT64_C(70331)};
    for (size_t slice = 0u; equal && slice < sizeof(future_budgets) / sizeof(future_budgets[0]); ++slice) {
        gbb_audio_frame source_audio[FORK_AUDIO_CAPACITY], target_audio[FORK_AUDIO_CAPACITY];
        size_t source_count = 0u, target_count = 0u;
        const gbb_run_result source_run = gbb_run_audio(source, future_budgets[slice],
            source_audio, FORK_AUDIO_CAPACITY, &source_count);
        const gbb_run_result target_run = gbb_run_audio(target, future_budgets[slice],
            target_audio, FORK_AUDIO_CAPACITY, &target_count);
        const int run_equal = same_run(source_run, target_run);
        const int pcm_equal = source_count == target_count &&
            memcmp(source_audio, target_audio, source_count * sizeof(source_audio[0])) == 0;
        const int frame_equal = copy_frame_equal(source, target, profile);
        equal = run_equal && pcm_equal && frame_equal;
        if (!run_equal) fprintf(stderr, "state-fork discrepancy case=%s observation=run-result\n", case_id);
        if (!pcm_equal) fprintf(stderr, "state-fork discrepancy case=%s observation=pcm\n", case_id);
        if (!frame_equal) fprintf(stderr, "state-fork discrepancy case=%s observation=frame-and-metadata\n", case_id);
        if (!equal) fprintf(stderr,
            "state-fork mismatch: immediate case=%s slice=%zu run=%d pcm=%d frame=%d counts=%zu/%zu consumed=%llu/%llu reason=%d/%d\n",
            case_id, slice, run_equal, pcm_equal, frame_equal, source_count,
            target_count, (unsigned long long)source_run.consumed_half_dots,
            (unsigned long long)target_run.consumed_half_dots,
            (int)source_run.reason, (int)target_run.reason);
        uint8_t *source_battery = NULL, *target_battery = NULL;
        size_t source_battery_size = 0u, target_battery_size = 0u;
        gbb_error source_battery_status = GBB_OK, target_battery_status = GBB_OK;
        gbb_error source_rumble_status = GBB_OK, target_rumble_status = GBB_OK;
        uint8_t source_rumble = 0u, target_rumble = 0u;
        uint64_t source_rumble_changes = 0u, target_rumble_changes = 0u;
        uint64_t source_battery_generation = 0u, target_battery_generation = 0u;
        int projection_equal = copy_battery(source, &source_battery, &source_battery_size,
                                      &source_battery_status) &&
            copy_battery(target, &target_battery, &target_battery_size,
                         &target_battery_status) &&
            source_battery_status == target_battery_status &&
            source_battery_size == target_battery_size &&
            (source_battery_size == 0u ||
             memcmp(source_battery, target_battery, source_battery_size) == 0) &&
            copy_rumble(source, &source_rumble_status, &source_rumble,
                        &source_rumble_changes) &&
            copy_rumble(target, &target_rumble_status, &target_rumble,
                        &target_rumble_changes) &&
            source_rumble_status == target_rumble_status &&
            (source_rumble_status != GBB_OK || source_rumble == target_rumble);
        if (projection_equal && source_battery_status == GBB_OK) {
            projection_equal = gbb_battery_generation(source, &source_battery_generation) == GBB_OK &&
                gbb_battery_generation(target, &target_battery_generation) == GBB_OK &&
                observer_delta(source_battery_base, source_battery_generation) ==
                    observer_delta(target_battery_base, target_battery_generation);
        }
        if (projection_equal && source_rumble_status == GBB_OK) {
            projection_equal = observer_delta(source_rumble_base, source_rumble_changes) ==
                observer_delta(target_rumble_base, target_rumble_changes);
        }
        if (!projection_equal) fprintf(stderr,
            "state-fork mismatch: projections case=%s slice=%zu battery=%d rumble=%d local=%llu/%llu,%llu/%llu\n",
            case_id, slice, source_battery_status == target_battery_status &&
                source_battery_size == target_battery_size,
            source_rumble_status == target_rumble_status && source_rumble == target_rumble,
            (unsigned long long)(source_battery_status == GBB_OK ? observer_delta(source_battery_base, source_battery_generation) : 0u),
            (unsigned long long)(target_battery_status == GBB_OK ? observer_delta(target_battery_base, target_battery_generation) : 0u),
            (unsigned long long)(source_rumble_status == GBB_OK ? observer_delta(source_rumble_base, source_rumble_changes) : 0u),
            (unsigned long long)(target_rumble_status == GBB_OK ? observer_delta(target_rumble_base, target_rumble_changes) : 0u));
        if (!projection_equal) {
            const int battery_projection_equal = source_battery_status == target_battery_status &&
                source_battery_size == target_battery_size &&
                (source_battery_size == 0u ||
                 memcmp(source_battery, target_battery, source_battery_size) == 0);
            const int rumble_projection_equal = source_rumble_status == target_rumble_status &&
                (source_rumble_status != GBB_OK || source_rumble == target_rumble);
            const int battery_delta_equal = source_battery_status != GBB_OK ||
                observer_delta(source_battery_base, source_battery_generation) ==
                observer_delta(target_battery_base, target_battery_generation);
            const int rumble_delta_equal = source_rumble_status != GBB_OK ||
                observer_delta(source_rumble_base, source_rumble_changes) ==
                observer_delta(target_rumble_base, target_rumble_changes);
            if (!battery_projection_equal || !battery_delta_equal)
                fprintf(stderr, "state-fork discrepancy case=%s observation=battery-projection-or-generation-delta\n", case_id);
            if (!rumble_projection_equal || !rumble_delta_equal)
                fprintf(stderr, "state-fork discrepancy case=%s observation=rumble-line-or-counter-delta\n", case_id);
        }
        equal = equal && projection_equal;
        free(target_battery); free(source_battery);
    }

    const gbb_error final_source_save = gbb_save_state(source, source_final, state_size);
    const gbb_error final_target_save = gbb_save_state(target, target_final, state_size);
    const int final_bytes_equal = final_source_save == GBB_OK && final_target_save == GBB_OK &&
        memcmp(source_final, target_final, state_size) == 0;
    if (!final_bytes_equal && final_source_save == GBB_OK && final_target_save == GBB_OK) {
        const size_t fields = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
        for (size_t f = 0u; f < fields; ++f) {
            const size_t count = state_field_count_for_instance(source, &STATE_FIELDS[f]);
            for (size_t i = 0u; i < count; ++i) {
                uint64_t left = 0u, right = 0u;
                if (state_host_value(source, &STATE_FIELDS[f], i, &left) &&
                    state_host_value(target, &STATE_FIELDS[f], i, &right) && left != right)
                    fprintf(stderr, "state-fork canonical-field-difference id=%s index=%zu source=%016llx target=%016llx\n",
                        STATE_FIELDS[f].path, i, (unsigned long long)left,
                        (unsigned long long)right);
            }
        }
    }
    const int final_saved = final_bytes_equal;
    if (!final_bytes_equal)
        fprintf(stderr, "state-fork discrepancy case=%s observation=final-canonical-state-bytes\n", case_id);
    if (!final_saved) fprintf(stderr, "state-fork mismatch: final canonical bytes case=%s source_status=%d target_status=%d\n",
        case_id, (int)final_source_save, (int)final_target_save);
    equal = equal && post_load_canonical_equal && final_saved;
    if (!equal) fprintf(stderr, "state-fork mismatch: canonical-state-bytes/output case=%s\n", case_id);
    else printf("state-fork pass case=%s profile=%u mode=%u state_bytes=%zu\n",
        case_id, (unsigned)profile, (unsigned)source->exec_mode, state_size);

    free(new_battery); free(old_battery); free(target_final); free(source_final); free(saved);
    gbb_destroy(target);
    gbb_destroy(baseline);
    gbb_destroy(source);
    return equal ? 0 : 1;
}

static int state_slice_invariance(void) {
    static const uint8_t loop_rom[0x8000] = {
        [0x100] = 0xC3u, [0x101] = 0x00u, [0x102] = 0x02u,
        [0x200] = 0x00u, [0x201] = 0x18u, [0x202] = 0xFDu
    };
    uint8_t rom[sizeof(loop_rom)];
    memcpy(rom, loop_rom, sizeof(rom));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    gbb_instance *whole = NULL, *sliced = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &whole) != GBB_OK ||
        gbb_load_rom(whole, rom, sizeof(rom)) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &sliced) != GBB_OK ||
        gbb_load_rom(sliced, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(sliced); gbb_destroy(whole);
        return 2;
    }
    gbb_audio_frame expected[FORK_AUDIO_CAPACITY], actual[FORK_AUDIO_CAPACITY];
    size_t expected_count = 0u, actual_count = 0u;
    const uint64_t total = UINT64_C(140448);
    const gbb_run_result expected_run = gbb_run_audio(whole, total, expected,
        FORK_AUDIO_CAPACITY, &expected_count);
    const uint64_t cuts[] = {1u, 7u, 16381u, 32769u, 81919u};
    uint64_t left = total;
    for (size_t i = 0u; i < sizeof(cuts) / sizeof(cuts[0]) && left != 0u; ++i) {
        const uint64_t budget = cuts[i] < left ? cuts[i] : left;
        gbb_audio_frame part[FORK_AUDIO_CAPACITY];
        size_t part_count = 0u;
        const gbb_run_result part_result = gbb_run_audio(sliced, budget, part,
            FORK_AUDIO_CAPACITY, &part_count);
        if (part_result.reason == GBB_STOP_INVALID_STATE ||
            part_count > FORK_AUDIO_CAPACITY - actual_count) {
            gbb_destroy(sliced); gbb_destroy(whole);
            return 1;
        }
        memcpy(actual + actual_count, part, part_count * sizeof(part[0]));
        actual_count += part_count;
        left -= part_result.consumed_half_dots;
        if (part_result.consumed_half_dots == 0u) break;
    }
    if (left != 0u) {
        gbb_audio_frame tail[FORK_AUDIO_CAPACITY];
        size_t tail_count = 0u;
        const gbb_run_result tail_result = gbb_run_audio(sliced, left, tail,
            FORK_AUDIO_CAPACITY, &tail_count);
        if (tail_result.consumed_half_dots != left ||
            tail_count > FORK_AUDIO_CAPACITY - actual_count) {
            gbb_destroy(sliced); gbb_destroy(whole);
            return 1;
        }
        memcpy(actual + actual_count, tail, tail_count * sizeof(tail[0]));
        actual_count += tail_count;
    }
    size_t state_size = 0u;
    uint8_t *a = NULL, *b = NULL;
    const int ok = expected_run.consumed_half_dots == total &&
        gbb_state_size(whole, &state_size) == GBB_OK &&
        gbb_state_size(sliced, &state_size) == GBB_OK &&
        (a = (uint8_t *)malloc(state_size)) != NULL &&
        (b = (uint8_t *)malloc(state_size)) != NULL &&
        gbb_save_state(whole, a, state_size) == GBB_OK &&
        gbb_save_state(sliced, b, state_size) == GBB_OK &&
        expected_count == actual_count &&
        memcmp(expected, actual, expected_count * sizeof(expected[0])) == 0 &&
        memcmp(a, b, state_size) == 0;
    if (!ok) fputs("state-slice-invariance mismatch\n", stderr);
    else puts("state-slice-invariance pass property=slice-invariance state=separate-from-fork");
    free(b); free(a);
    gbb_destroy(sliced); gbb_destroy(whole);
    return ok ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "state_slice_invariance") == 0)
        return state_slice_invariance();
    if (argc >= 5 && strcmp(argv[1], "case") == 0) {
        uint64_t prefix_budget = UINT64_C(140448);
        for (int arg = 5; arg < argc; ++arg) {
            if (strcmp(argv[arg], "--budget") == 0 && arg + 1 < argc) {
                uint64_t value = 0u;
                const char *digits = argv[++arg];
                if (*digits == '\0') return 2;
                for (; *digits != '\0'; ++digits) {
                    if (*digits < '0' || *digits > '9') return 2;
                    const uint64_t digit = (uint64_t)(*digits - '0');
                    if (value > (UINT64_MAX - digit) / 10u) return 2;
                    value = value * 10u + digit;
                }
                if (value == 0u) return 2;
                prefix_budget = value;
            }
#ifdef GBB_STATE_FORK_MUTANT
            else if (strcmp(argv[arg], "--mutant") == 0 && arg + 1 < argc &&
                     state_fork_mutant_field == NULL) {
                state_fork_mutant_field = argv[++arg];
            }
#endif
            else return 2;
        }
        const gbb_profile profile = strcmp(argv[4], "cgb") == 0
            ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B;
        if (strcmp(argv[4], "cgb") != 0 && strcmp(argv[4], "dmg") != 0) return 2;
        return state_fork_case(argv[2], argv[3], profile, prefix_budget);
    }
    if (argc >= 4 && strcmp(argv[1], "generated_fields") == 0) {
        const int cgb = strcmp(argv[3], "cgb") == 0;
        if (!cgb && strcmp(argv[3], "dmg") != 0) return 2;
        uint64_t prefix_budget = UINT64_C(140448);
        for (int arg = 4; arg < argc; ++arg) {
            if (strcmp(argv[arg], "--budget") == 0 && arg + 1 < argc) {
                uint64_t value = 0u;
                const char *digits = argv[++arg];
                if (*digits == '\0') return 2;
                for (; *digits != '\0'; ++digits) {
                    if (*digits < '0' || *digits > '9') return 2;
                    const uint64_t digit = (uint64_t)(*digits - '0');
                    if (value > (UINT64_MAX - digit) / 10u) return 2;
                    value = value * 10u + digit;
                }
                if (value == 0u) return 2;
                prefix_budget = value;
            }
#ifdef GBB_STATE_FORK_MUTANT
            else if (strcmp(argv[arg], "--mutant") == 0 && arg + 1 < argc &&
                     state_fork_mutant_field == NULL) {
                state_fork_mutant_field = argv[++arg];
            }
#endif
            else return 2;
        }
        uint8_t *rom = NULL;
        size_t rom_size = 0u;
        if (!generated_rom(argv[2], &rom, &rom_size)) return 2;
        char sha256[65];
        generated_rom_sha256(rom, rom_size, sha256);
        printf("generated-rom id=%s profile=%s size=%zu sha256=%s\n",
            argv[2], cgb ? "cgb" : "dmg", rom_size, sha256);
        free(rom);
        char generated_path[64];
        const int path_size = snprintf(generated_path, sizeof(generated_path),
                                       "@generated/%s", argv[2]);
        if (path_size < 0 || (size_t)path_size >= sizeof(generated_path)) return 2;
        char generated_case_id[96];
        const int id_size = snprintf(generated_case_id, sizeof(generated_case_id),
            "generated:%s:%s", argv[2], cgb ? "cgb" : "dmg");
        if (id_size < 0 || (size_t)id_size >= sizeof(generated_case_id)) return 2;
        return state_fork_case(generated_case_id, generated_path,
            cgb ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B, prefix_budget);
    }
    fprintf(stderr, "usage: test_state_fork state_slice_invariance | case ID ROM dmg|cgb [--budget HALF_DOTS] [--mutant FIELD] | generated_fields ID dmg|cgb [--budget HALF_DOTS] [--mutant FIELD]\n");
    return 2;
}
