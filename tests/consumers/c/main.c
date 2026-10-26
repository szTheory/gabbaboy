#include <gabbaboy/gabbaboy.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STATE_ASSERT_ERROR(name, value) _Static_assert((name) == (value), #name " changed value")
STATE_ASSERT_ERROR(GBB_OK, 0);
STATE_ASSERT_ERROR(GBB_INVALID_ARGUMENT, 1);
STATE_ASSERT_ERROR(GBB_UNSUPPORTED_PROFILE, 2);
STATE_ASSERT_ERROR(GBB_INVALID_ROM, 3);
STATE_ASSERT_ERROR(GBB_ROM_TRUNCATED, 4);
STATE_ASSERT_ERROR(GBB_ROM_TOO_LARGE, 5);
STATE_ASSERT_ERROR(GBB_ROM_SIZE_MISMATCH, 6);
STATE_ASSERT_ERROR(GBB_UNSUPPORTED_CARTRIDGE, 7);
STATE_ASSERT_ERROR(GBB_UNSUPPORTED_CARTRIDGE_VARIANT, 8);
STATE_ASSERT_ERROR(GBB_UNSUPPORTED_ROM_SIZE, 9);
STATE_ASSERT_ERROR(GBB_UNSUPPORTED_RAM_SIZE, 10);
STATE_ASSERT_ERROR(GBB_NO_BATTERY, 11);
STATE_ASSERT_ERROR(GBB_BUFFER_TOO_SMALL, 12);
STATE_ASSERT_ERROR(GBB_BATTERY_SIZE_MISMATCH, 13);
STATE_ASSERT_ERROR(GBB_OUT_OF_MEMORY, 14);
STATE_ASSERT_ERROR(GBB_EVENT_QUEUE_FULL, 15);
STATE_ASSERT_ERROR(GBB_INVALID_EVENT, 16);
STATE_ASSERT_ERROR(GBB_FRAME_NOT_READY, 17);
STATE_ASSERT_ERROR(GBB_NO_RUMBLE, 18);
STATE_ASSERT_ERROR(GBB_NO_RTC, 19);
STATE_ASSERT_ERROR(GBB_UNSUPPORTED_EXECUTION_MODE, 20);
STATE_ASSERT_ERROR(GBB_STATE_NO_ROM, 21);
STATE_ASSERT_ERROR(GBB_STATE_BAD_FORMAT, 22);
STATE_ASSERT_ERROR(GBB_STATE_UNSUPPORTED_VERSION, 23);
STATE_ASSERT_ERROR(GBB_STATE_IDENTITY_MISMATCH, 24);
STATE_ASSERT_ERROR(GBB_STATE_SIZE_MISMATCH, 25);
STATE_ASSERT_ERROR(GBB_STATE_CORRUPT, 26);
STATE_ASSERT_ERROR(GBB_STATE_INVALID_CONTENT, 27);
#undef STATE_ASSERT_ERROR

static gbb_error (*const state_size_api)(const gbb_instance *, size_t *) = gbb_state_size;
static gbb_error (*const save_state_api)(const gbb_instance *, uint8_t *, size_t) = gbb_save_state;
static gbb_error (*const load_state_api)(gbb_instance *, const uint8_t *, size_t) = gbb_load_state;

static uint32_t state_smoke_crc_update(uint32_t crc, const uint8_t *bytes, size_t length) {
    for (size_t i = 0u; i < length; ++i) {
        crc ^= bytes[i];
        for (unsigned bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ? UINT32_C(0xEDB88320) : 0u);
    }
    return crc;
}

static void state_smoke_rechecksum(uint8_t *bytes, size_t total_size) {
    uint32_t crc = state_smoke_crc_update(UINT32_MAX, bytes, 60u);
    crc = state_smoke_crc_update(crc, bytes + 64u, total_size - 64u) ^ UINT32_MAX;
    for (unsigned i = 0u; i < 4u; ++i) bytes[60u + i] = (uint8_t)(crc >> (i * 8u));
}

static int state_smoke_same_run(gbb_run_result left, gbb_run_result right) {
    return left.consumed_half_dots == right.consumed_half_dots && left.reason == right.reason &&
           left.trace_count == right.trace_count && left.diagnostic_count == right.diagnostic_count &&
           left.lockup_pc == right.lockup_pc && left.lockup_opcode == right.lockup_opcode;
}

static int state_smoke_run_audio(gbb_instance *instance, uint64_t budget,
                                 gbb_audio_frame *frames, size_t capacity,
                                 size_t *count, gbb_run_result *result) {
    *result = gbb_run_audio(instance, budget, frames, capacity, count);
    return result->reason == GBB_STOP_BUDGET && result->consumed_half_dots <= budget &&
           result->consumed_half_dots != 0u;
}

static int state_smoke_refusal(gbb_instance *instance, const uint8_t *bytes, size_t length,
                               size_t state_size, gbb_error expected) {
    uint8_t *before = malloc(state_size);
    uint8_t *after = malloc(state_size);
    int unchanged = 0;
    if (before != NULL && after != NULL &&
        save_state_api(instance, before, state_size) == GBB_OK &&
        load_state_api(instance, bytes, length) == expected &&
        save_state_api(instance, after, state_size) == GBB_OK &&
        memcmp(before, after, state_size) == 0) unchanged = 1;
    free(before);
    free(after);
    return unchanged;
}

/* Public-only installed state API, exact errors/signatures and continuation smoke. */
static int state_api_smoke(void) {
    enum { ROM_BYTES = 32768, STATE_HEADER_BYTES = 64, AUDIO_CAPACITY = 2048 };
    static const uint8_t program[] = {
        0x21u, 0x00u, 0xC0u, 0x3Eu, 0x5Au, 0x77u, 0x23u,
        0x3Eu, 0xA5u, 0x77u, 0x18u, 0xFEu
    };
    uint8_t rom[ROM_BYTES] = {0};
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    memcpy(rom + 0x150u, program, sizeof(program));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    gbb_instance *source = NULL, *target = NULL;
    gbb_audio_frame prefix_source[AUDIO_CAPACITY], prefix_target[AUDIO_CAPACITY];
    gbb_audio_frame future_source[AUDIO_CAPACITY], future_target[AUDIO_CAPACITY];
    size_t prefix_source_count = 0u, prefix_target_count = 0u;
    size_t future_source_count = 0u, future_target_count = 0u;
    gbb_run_result prefix_source_run = {0}, prefix_target_run = {0};
    gbb_run_result future_source_run = {0}, future_target_run = {0};
    uint8_t no_rom_output[STATE_HEADER_BYTES + 4u];
    size_t output_size = 731u;
    uint8_t *snapshot = NULL, *mutated = NULL, *expected = NULL, *actual = NULL;
    size_t state_size = 0u, target_size = 0u;
    int passed = 0;
    int stage = 1;

    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &source) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &target) != GBB_OK) goto done;
    if (state_size_api(source, &output_size) != GBB_STATE_NO_ROM || output_size != 731u ||
        state_size_api(source, NULL) != GBB_INVALID_ARGUMENT) goto done;
    memset(no_rom_output, 0xA5, sizeof(no_rom_output));
    if (save_state_api(source, no_rom_output, sizeof(no_rom_output)) != GBB_STATE_NO_ROM) goto done;
    for (size_t i = 0u; i < sizeof(no_rom_output); ++i)
        if (no_rom_output[i] != 0xA5u) goto done;
    if (load_state_api(source, no_rom_output, STATE_HEADER_BYTES - 1u) != GBB_STATE_BAD_FORMAT ||
        load_state_api(source, NULL, STATE_HEADER_BYTES) != GBB_INVALID_ARGUMENT) goto done;

    stage = 2;
    if (gbb_load_rom(source, rom, sizeof(rom)) != GBB_OK ||
        gbb_load_rom(target, rom, sizeof(rom)) != GBB_OK) goto done;
    if (state_size_api(source, &state_size) != GBB_OK || state_size <= STATE_HEADER_BYTES ||
        state_size_api(target, &target_size) != GBB_OK || target_size != state_size) goto done;
    snapshot = malloc(state_size);
    mutated = malloc(state_size);
    expected = malloc(state_size);
    actual = malloc(state_size);
    if (snapshot == NULL || mutated == NULL || expected == NULL || actual == NULL) goto done;

    memset(mutated, 0xA5, state_size);
    if (save_state_api(source, mutated, state_size - 1u) != GBB_BUFFER_TOO_SMALL) goto done;
    for (size_t i = 0u; i < state_size; ++i)
        if (mutated[i] != 0xA5u) goto done;
    stage = 3;
    if (!state_smoke_run_audio(source, UINT64_C(100000), prefix_source, AUDIO_CAPACITY,
                               &prefix_source_count, &prefix_source_run)) {
        fprintf(stderr, "state prefix source failed reason=%d consumed=%llu count=%zu\n",
                prefix_source_run.reason, (unsigned long long)prefix_source_run.consumed_half_dots,
                prefix_source_count); goto done;
    }
    if (!state_smoke_run_audio(target, UINT64_C(100000), prefix_target, AUDIO_CAPACITY,
                               &prefix_target_count, &prefix_target_run)) {
        fprintf(stderr, "state prefix target failed reason=%d consumed=%llu count=%zu\n",
                prefix_target_run.reason, (unsigned long long)prefix_target_run.consumed_half_dots,
                prefix_target_count); goto done;
    }
    if (!state_smoke_same_run(prefix_source_run, prefix_target_run) ||
        prefix_source_count != prefix_target_count ||
        memcmp(prefix_source, prefix_target, prefix_source_count * sizeof(prefix_source[0])) != 0) {
        fprintf(stderr, "state prefix twins diverged\n"); goto done;
    }
    if (gbb_peek_ram(source, 0xC000u) != 0x5Au || gbb_peek_ram(source, 0xC001u) != 0xA5u) {
        fprintf(stderr, "state prefix guest marker mismatch: %02X %02X\n",
                gbb_peek_ram(source, 0xC000u), gbb_peek_ram(source, 0xC001u)); goto done;
    }

    stage = 4;
    memset(mutated, 0xA5, state_size + 0u);
    if (save_state_api(source, mutated, state_size) != GBB_OK ||
        memcmp(mutated, "GBBS", 4u) != 0) goto done;
    memcpy(snapshot, mutated, state_size);
    {
        uint8_t tail[8];
        uint8_t *with_tail = malloc(state_size + sizeof(tail));
        if (with_tail == NULL) goto done;
        memset(with_tail, 0xA5, state_size + sizeof(tail));
        if (save_state_api(source, with_tail, state_size + sizeof(tail)) != GBB_OK) {
            free(with_tail); goto done;
        }
        for (size_t i = state_size; i < state_size + sizeof(tail); ++i)
            if (with_tail[i] != 0xA5u) { free(with_tail); goto done; }
        free(with_tail);
    }

    stage = 5;
    if (!state_smoke_refusal(target, snapshot, state_size - 1u, state_size, GBB_STATE_SIZE_MISMATCH))
        goto done;
    memcpy(mutated, snapshot, state_size); mutated[0] = (uint8_t)'X';
    if (!state_smoke_refusal(target, mutated, state_size, state_size, GBB_STATE_BAD_FORMAT)) goto done;
    memcpy(mutated, snapshot, state_size); mutated[4] = 2u;
    if (!state_smoke_refusal(target, mutated, state_size, state_size, GBB_STATE_UNSUPPORTED_VERSION)) goto done;
    memcpy(mutated, snapshot, state_size); mutated[20] ^= 1u;
    mutated[52] = 0u; mutated[53] = 0u; mutated[54] = 0u; mutated[55] = 0u;
    if (!state_smoke_refusal(target, mutated, state_size, state_size, GBB_STATE_IDENTITY_MISMATCH)) goto done;
    memcpy(mutated, snapshot, state_size); mutated[STATE_HEADER_BYTES] ^= 1u;
    if (!state_smoke_refusal(target, mutated, state_size, state_size, GBB_STATE_CORRUPT)) goto done;
    memcpy(mutated, snapshot, state_size); mutated[18] = 1u;
    state_smoke_rechecksum(mutated, state_size);
    if (!state_smoke_refusal(target, mutated, state_size, state_size, GBB_STATE_INVALID_CONTENT)) goto done;

    stage = 6;
    if (!state_smoke_run_audio(source, UINT64_C(200000), future_source, AUDIO_CAPACITY,
                               &future_source_count, &future_source_run) ||
        !state_smoke_run_audio(target, UINT64_C(200000), future_target, AUDIO_CAPACITY,
                               &future_target_count, &future_target_run) ||
        !state_smoke_same_run(future_source_run, future_target_run) ||
        future_source_count != future_target_count ||
        memcmp(future_source, future_target, future_source_count * sizeof(future_source[0])) != 0 ||
        save_state_api(source, expected, state_size) != GBB_OK ||
        save_state_api(target, actual, state_size) != GBB_OK || memcmp(expected, actual, state_size) != 0)
        goto done;

    stage = 7;
    if (gbb_reset(target) != GBB_OK || load_state_api(target, snapshot, state_size) != GBB_OK ||
        state_size_api(target, &target_size) != GBB_OK || target_size != state_size ||
        !state_smoke_run_audio(target, UINT64_C(200000), future_target, AUDIO_CAPACITY,
                               &future_target_count, &future_target_run) ||
        !state_smoke_same_run(future_source_run, future_target_run) ||
        future_source_count != future_target_count ||
        memcmp(future_source, future_target, future_source_count * sizeof(future_source[0])) != 0 ||
        save_state_api(target, actual, state_size) != GBB_OK || memcmp(expected, actual, state_size) != 0)
        goto done;
    printf("state_api_smoke pass bytes=%zu prefix_audio=%zu future_audio=%zu\n",
           state_size, prefix_source_count, future_source_count);
    passed = 1;

done:
    if (!passed) fprintf(stderr, "state_api_smoke failed at stage=%d state_size=%zu\n", stage, state_size);
    free(snapshot); free(mutated); free(expected); free(actual);
    gbb_destroy(source); gbb_destroy(target);
    return passed ? 0 : 1;
}

static int battery_api_smoke(void) {
    enum { ROM_BYTES = 32768, RAM_BYTES = 8192 };
    uint8_t rom[ROM_BYTES] = {0};
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    gbb_instance *machine = NULL;
    uint8_t input[RAM_BYTES];
    uint8_t output[RAM_BYTES + 2u];
    int passed = 0;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;
    size_t size = 0u;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != RAM_BYTES) goto done;
    memset(output, 0xA7, sizeof(output));
    if (gbb_copy_battery(machine, output + 1u, RAM_BYTES - 1u) !=
        GBB_BUFFER_TOO_SMALL) goto done;
    for (size_t i = 0u; i < sizeof(output); ++i)
        if (output[i] != 0xA7u) goto done;
    if (gbb_copy_battery(machine, output + 1u, RAM_BYTES) != GBB_OK) goto done;
    for (size_t i = 0u; i < RAM_BYTES; ++i)
        if (output[i + 1u] != 0xFFu) goto done;
    if (output[0] != 0xA7u || output[sizeof(output) - 1u] != 0xA7u) goto done;

    for (size_t i = 0u; i < RAM_BYTES; ++i)
        input[i] = (uint8_t)(i * 37u + 0x31u);
    if (gbb_import_battery(machine, input, sizeof(input)) != GBB_OK) goto done;
    uint64_t generation = 0u;
    if (gbb_battery_generation(machine, &generation) != GBB_OK || generation != 1u)
        goto done;
    if (gbb_import_battery(machine, input, sizeof(input) - 1u) !=
        GBB_BATTERY_SIZE_MISMATCH) goto done;
    memset(output, 0x5C, sizeof(output));
    if (gbb_copy_battery(machine, output + 1u, RAM_BYTES) != GBB_OK ||
        memcmp(output + 1u, input, sizeof(input)) != 0 ||
        output[0] != 0x5Cu || output[sizeof(output) - 1u] != 0x5Cu ||
        gbb_battery_generation(machine, &generation) != GBB_OK || generation != 1u)
        goto done;
    /* The installed header and library export gbb_rumble_state; a non-rumble
     * cartridge reports GBB_NO_RUMBLE and leaves the outputs alone. */
    {
        uint8_t rumble_on = 0xA5u;
        uint64_t rumble_changes = UINT64_C(0x1122334455667788);
        if (gbb_rumble_state(machine, &rumble_on, &rumble_changes) != GBB_NO_RUMBLE ||
            rumble_on != 0xA5u || rumble_changes != UINT64_C(0x1122334455667788))
            goto done;
    }
    passed = 1;

done:
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

/* Installed-package CGB profile smoke: create, probe, info and the PGB/frame refusals. */
static int cgb_api_smoke(void) {
    enum { ROM_BYTES = 32768 };
    uint8_t rom[ROM_BYTES] = {0};
    rom[0x143u] = 0xC0u;
    rom[0x147u] = 0x00u;
    {
        uint8_t checksum = 0u;
        for (size_t i = 0x134u; i <= 0x14Cu; ++i)
            checksum = (uint8_t)(checksum - rom[i] - 1u);
        rom[0x14Du] = checksum;
    }

    gbb_instance *machine = NULL;
    gbb_info info;
    int passed = 0;
    /* $C0 on the DMG profile: informational flag, DMG mode. */
    memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, rom, sizeof(rom), &info) != GBB_OK ||
        info.mode != GBB_MODE_DMG || (info.flags & GBB_INFO_CGB_ONLY_ON_DMG) == 0u ||
        info.struct_size != GBB_INFO_SIZE_V1) goto done;
    /* The CGB profile creates, loads and reports CGB mode. */
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;
    memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_get_info(machine, &info) != GBB_OK || info.mode != GBB_MODE_CGB ||
        info.profile != 2u || info.struct_size != GBB_INFO_SIZE_V1 ||
        info.cgb_support != GBB_CGB_SUPPORT_ONLY) goto done;
    /* A zero struct_size is rejected and leaves every other byte alone. */
    {
        gbb_info zero;
        uint8_t raw[sizeof(gbb_info)];
        memset(&zero, 0xA7, sizeof(zero));
        zero.struct_size = 0u;
        memcpy(raw, &zero, sizeof(raw));
        if (gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, rom, sizeof(rom), &zero) != GBB_INVALID_ARGUMENT ||
            memcmp(raw, &zero, sizeof(raw)) != 0)
            goto done;
    }
    /* A PGB-flagged image is refused by the CGB profile on both probe and load. */
    rom[0x143u] = 0x84u;
    {
        uint8_t checksum = 0u;
        for (size_t i = 0x134u; i <= 0x14Cu; ++i)
            checksum = (uint8_t)(checksum - rom[i] - 1u);
        rom[0x14Du] = checksum;
    }
    memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, rom, sizeof(rom), &info) !=
            GBB_UNSUPPORTED_EXECUTION_MODE ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_UNSUPPORTED_EXECUTION_MODE) goto done;
    /* The shade call is refused on the CGB profile; colour is read with the RGB555 call. */
    {
        uint8_t pixels[160 * 144];
        gbb_frame_info frame;
        if (gbb_copy_frame(machine, pixels, sizeof(pixels), 160u, &frame) !=
            GBB_UNSUPPORTED_PROFILE) goto done;
    }
    {
        static uint16_t rgb[160u * 144u];
        gbb_frame_info frame;
        gbb_instance *dmg = NULL;
        gbb_compat_palette palette;
        gbb_compat_palette override_palette;
        int colour_ok = 0;
        /* The refused PGB load left the earlier CGB image in place; run two frames of it. */
        for (int i = 0; i < 2; ++i) gbb_run(machine, UINT64_C(140448), NULL, 0);
        if (gbb_copy_frame_rgb555(machine, rgb, sizeof(rgb), 320u, &frame) != GBB_OK ||
            frame.width != 160u || frame.height != 144u || frame.generation == 0u) goto colour_done;
        for (size_t i = 0; i < 160u * 144u; ++i)
            if (rgb[i] > 0x7FFFu) goto colour_done;
        memset(rgb, 0xA7, sizeof(rgb));
        if (gbb_copy_frame_rgb555(machine, rgb, sizeof(rgb), 319u, &frame) != GBB_INVALID_ARGUMENT ||
            ((const uint8_t *)rgb)[0] != 0xA7u) goto colour_done;
        if (gbb_create(GBB_PROFILE_DMG_CPU_B, &dmg) != GBB_OK ||
            gbb_copy_frame_rgb555(dmg, rgb, sizeof(rgb), 320u, &frame) != GBB_UNSUPPORTED_PROFILE)
            goto colour_done;
        memset(&palette, 0, sizeof(palette));
        palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
        if (gbb_get_compat_palette(machine, &palette) != GBB_OK ||
            palette.struct_size != GBB_COMPAT_PALETTE_SIZE_V1) goto colour_done;
        override_palette = palette;
        override_palette.bg[0] = 0x1234u;
        if (gbb_set_compat_palette(machine, &override_palette) != GBB_OK) goto colour_done;
        override_palette.bg[1] = 0x8000u;
        if (gbb_set_compat_palette(machine, &override_palette) != GBB_INVALID_ARGUMENT) goto colour_done;
        if (gbb_get_compat_palette(machine, &palette) != GBB_OK || palette.bg[0] != 0x1234u ||
            palette.bg[1] == 0x8000u) goto colour_done;
        if (gbb_set_compat_palette(machine, NULL) != GBB_OK) goto colour_done;
        colour_ok = 1;
colour_done:
        gbb_destroy(dmg);
        if (!colour_ok) goto done;
    }
    passed = 1;

done:
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

/* Build a self-contained, ROM-only CGB guest for the installed public API. */
static void cgb_speed_fill_rom(uint8_t *rom, size_t size, uint8_t key1_value) {
    memset(rom, 0, size);
    rom[0x100u] = 0xC3u; /* JP $0150 */
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x143u] = 0xC0u; /* CGB-only */
    rom[0x147u] = 0x00u; /* ROM-only cartridge */
    rom[0x148u] = 0x00u; /* 32 KiB ROM */
    rom[0x149u] = 0x00u; /* no external RAM */
    rom[0x150u] = 0x3Eu; /* LD A,$55: mark execution before STOP. */
    rom[0x151u] = 0x55u;
    rom[0x152u] = 0xEAu; /* LD ($C000),A */
    rom[0x153u] = 0x00u;
    rom[0x154u] = 0xC0u;
    rom[0x155u] = 0x3Eu; /* LD A,key1_value */
    rom[0x156u] = key1_value;
    rom[0x157u] = 0xE0u; /* LDH ($4D),A: arm only in the positive guest. */
    rom[0x158u] = 0x4Du;
    rom[0x159u] = 0x10u; /* STOP $00 */
    rom[0x15Au] = 0x00u;
    rom[0x15Bu] = 0xF0u; /* LDH A,($4D): read KEY1 after the switch. */
    rom[0x15Cu] = 0x4Du;
    rom[0x15Du] = 0xEAu; /* LD ($C000),A */
    rom[0x15Eu] = 0x00u;
    rom[0x15Fu] = 0xC0u;
    rom[0x160u] = 0x76u; /* HALT */
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* Returns true only when an armed switch reaches HALT through partitioned public runs. */
static int cgb_speed_partition_smoke(uint8_t key1_value, int *out_unarmed_rejected) {
    enum { ROM_BYTES = 32768u, SLICE_HALF_DOTS = 4096u, FRAME_HALF_DOTS = 140448u };
    const uint64_t cap_half_dots = UINT64_C(2) * FRAME_HALF_DOTS;
    uint8_t rom[ROM_BYTES];
    static uint16_t pixels[160u * 144u];
    gbb_instance *machine = NULL;
    gbb_run_result result = {0};
    gbb_frame_info frame = {0};
    gbb_error frame_error = GBB_FRAME_NOT_READY;
    uint64_t consumed_total = 0u;
    uint64_t full_slice_total = 0u;
    uint64_t halt_partial_half_dots = 0u;
    unsigned calls = 0u;
    int halted = 0;
    int frame_ready = 0;
    int passed = 0;
    if (out_unarmed_rejected != NULL) *out_unarmed_rejected = 0;
    cgb_speed_fill_rom(rom, sizeof(rom), key1_value);
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;

    result = gbb_run(machine, SLICE_HALF_DOTS, NULL, 0u);
    ++calls;
    consumed_total += result.consumed_half_dots;
    if (result.reason == GBB_STOP_STOPPED) {
        if (key1_value == 0u && result.consumed_half_dots > 0u &&
            result.consumed_half_dots <= SLICE_HALF_DOTS &&
            gbb_peek_ram(machine, 0xC000u) == 0x55u &&
            (gbb_peek_ram(machine, 0xC000u) & 0x80u) == 0u &&
            out_unarmed_rejected != NULL)
            *out_unarmed_rejected = 1;
        goto done;
    }
    if (key1_value == 0u || result.reason != GBB_STOP_BUDGET ||
        result.consumed_half_dots != SLICE_HALF_DOTS ||
        gbb_peek_ram(machine, 0xC000u) != 0x55u) goto done;
    full_slice_total += SLICE_HALF_DOTS;

    for (; calls < 69u; ++calls) {
        result = gbb_run(machine, SLICE_HALF_DOTS, NULL, 0u);
        consumed_total += result.consumed_half_dots;
        if (result.reason == GBB_STOP_HALTED_IDLE && !halted) halted = 1;
        if (result.reason == GBB_STOP_STOPPED && key1_value == 0u &&
            result.consumed_half_dots > 0u &&
            gbb_peek_ram(machine, 0xC000u) == 0x55u &&
            (gbb_peek_ram(machine, 0xC000u) & 0x80u) == 0u &&
            out_unarmed_rejected != NULL) {
            *out_unarmed_rejected = 1;
            goto done;
        }
        if ((!halted && result.reason != GBB_STOP_BUDGET) ||
            (halted && result.reason != GBB_STOP_HALTED_IDLE) ||
            result.consumed_half_dots == 0u ||
            result.consumed_half_dots > SLICE_HALF_DOTS) goto done;
        if (result.consumed_half_dots == SLICE_HALF_DOTS)
            full_slice_total += SLICE_HALF_DOTS;
        else if (halted)
            halt_partial_half_dots = result.consumed_half_dots;
        if (consumed_total > cap_half_dots) goto done;
        frame_error = gbb_copy_frame_rgb555(machine, pixels, sizeof(pixels), 320u, &frame);
        if (frame_error == GBB_OK) frame_ready = 1;
        else if (frame_error != GBB_FRAME_NOT_READY) goto done;
        if (halted && frame_ready) break;
    }
    if (!halted || !frame_ready ||
        consumed_total != full_slice_total + halt_partial_half_dots ||
        consumed_total > cap_half_dots ||
        (gbb_peek_ram(machine, 0xC000u) & 0x80u) == 0u ||
        frame.width != 160u || frame.height != 144u || frame.generation == 0u ||
        frame.completion_half_dots > consumed_total)
        goto done;
    passed = 1;

done:
    gbb_destroy(machine);
    return passed;
}

/* Execute a small original guest through the installed C API. The ROM is its
 * own GDMA source; the guest copies VRAM back to WRAM for public observation. */
static int cgb_dma_partition_smoke(int double_speed, int transfer_enabled,
                                   int *out_data_match, int *out_status_match,
                                   int *out_timing_match) {
    enum { ROM_BYTES = 32768u, SLICE_HALF_DOTS = 257u, DMA_BYTES = 128u,
           MAX_PARTITIONS = 600u };
    uint8_t rom[ROM_BYTES];
    gbb_instance *machine = NULL;
    uint64_t consumed = 0u;
    unsigned calls = 0u;
    int data_match = 1;
    int status_match = 0;
    int timing_match = 0;
    int passed = 0;
    int first_bad_byte = -1;
    int failure = 0;
    gbb_stop_reason last_reason = GBB_STOP_BUDGET;
    size_t pc = 0x150u;
    static const uint8_t normal_prefix[] = {
        0xAFu, 0xE0u, 0x04u,             /* Reset DIV before the DMA timing sentinel. */
        0x3Eu, 0x02u, 0xE0u, 0x51u,       /* FF51 source high = ROM $0200. */
        0xAFu, 0xE0u, 0x52u,             /* FF52 source low = $00. */
        0xAFu, 0xE0u, 0x53u,             /* FF53 destination high = $00. */
        0xAFu, 0xE0u, 0x54u,             /* FF54 destination low = $00. */
        0xF0u, 0x4Du, 0xEAu, 0x04u, 0xC1u /* Record speed-switch status. */
    };
    static const uint8_t double_speed_prefix[] = {
        0x3Eu, 0x01u, 0xE0u, 0x4Du,       /* Arm KEY1. */
        0x10u, 0x00u,                     /* STOP performs the CGB speed switch. */
        0xAFu, 0xE0u, 0x04u,
        0x3Eu, 0x02u, 0xE0u, 0x51u,
        0xAFu, 0xE0u, 0x52u,
        0xAFu, 0xE0u, 0x53u,
        0xAFu, 0xE0u, 0x54u,
        0xF0u, 0x4Du, 0xEAu, 0x04u, 0xC1u
    };
    const uint8_t *prefix = double_speed ? double_speed_prefix : normal_prefix;
    size_t prefix_size = double_speed ? sizeof(double_speed_prefix) : sizeof(normal_prefix);

    if (out_data_match != NULL) *out_data_match = 0;
    if (out_status_match != NULL) *out_status_match = 0;
    if (out_timing_match != NULL) *out_timing_match = 0;
    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = 0xC0u; rom[0x147u] = 0x00u;
    rom[0x148u] = 0x00u; rom[0x149u] = 0x00u;
    memcpy(rom + pc, prefix, prefix_size);
    pc += prefix_size;
    {
        rom[pc++] = 0xF0u; rom[pc++] = 0x41u; /* Wait for a real visible mode-3 entry. */
        rom[pc++] = 0xE6u; rom[pc++] = 0x03u;
        rom[pc++] = 0xFEu; rom[pc++] = 0x03u;
        rom[pc++] = 0x20u; rom[pc++] = 0xF8u;
    }
    rom[pc++] = 0xF0u; rom[pc++] = 0x04u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x00u; rom[pc++] = 0xC1u;
    if (transfer_enabled) {
        rom[pc++] = 0x3Eu; rom[pc++] = 0x07u; /* Start eight-block GDMA. */
        rom[pc++] = 0xE0u; rom[pc++] = 0x55u;
    }
    rom[pc++] = 0xF0u; rom[pc++] = 0x04u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x01u; rom[pc++] = 0xC1u;
    rom[pc++] = 0xF0u; rom[pc++] = 0x55u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x02u; rom[pc++] = 0xC1u;
    rom[pc++] = 0xAFu; rom[pc++] = 0xE0u; rom[pc++] = 0x40u; /* Unlock VRAM reads. */
    rom[pc++] = 0x21u; rom[pc++] = 0x00u; rom[pc++] = 0x80u; /* HL = VRAM. */
    rom[pc++] = 0x11u; rom[pc++] = 0x00u; rom[pc++] = 0xC2u; /* DE = WRAM readback. */
    rom[pc++] = 0x06u; rom[pc++] = (uint8_t)DMA_BYTES;
    rom[pc++] = 0x2Au; /* loop: LD A,(HL+) */
    rom[pc++] = 0x12u; /* LD (DE),A */
    rom[pc++] = 0x13u; /* INC DE */
    rom[pc++] = 0x05u; /* DEC B */
    rom[pc++] = 0x20u; rom[pc++] = 0xFAu; /* JR NZ,loop */
    rom[pc++] = 0x3Eu; rom[pc++] = 0xA5u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x03u; rom[pc++] = 0xC1u;
    rom[pc++] = 0x76u; /* HALT */
    for (size_t i = 0u; i < DMA_BYTES; ++i)
        rom[0x0200u + i] = (uint8_t)(i ^ 0x5Au);
    {
        uint8_t checksum = 0u;
        for (size_t i = 0x134u; i <= 0x14Cu; ++i)
            checksum = (uint8_t)(checksum - rom[i] - 1u);
        rom[0x14Du] = checksum;
    }
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) { failure = 1; goto done; }
    while (gbb_peek_ram(machine, 0xC103u) != 0xA5u && calls < MAX_PARTITIONS) {
        const gbb_run_result result = gbb_run(machine, SLICE_HALF_DOTS, NULL, 0u);
        ++calls;
        last_reason = result.reason;
        if (result.consumed_half_dots == 0u ||
            result.consumed_half_dots > SLICE_HALF_DOTS ||
            (result.reason != GBB_STOP_BUDGET && result.reason != GBB_STOP_HALTED_IDLE)) {
            failure = 2; goto done;
        }
        consumed += result.consumed_half_dots;
        if (consumed > (uint64_t)MAX_PARTITIONS * SLICE_HALF_DOTS) { failure = 3; goto done; }
    }
    if (gbb_peek_ram(machine, 0xC103u) != 0xA5u || calls < 2u) { failure = 4; goto done; }
    status_match = gbb_peek_ram(machine, 0xC102u) == 0xFFu;
    timing_match = (uint8_t)(gbb_peek_ram(machine, 0xC101u) -
                             gbb_peek_ram(machine, 0xC100u)) > 0u;
    if ((gbb_peek_ram(machine, 0xC104u) & 0x80u) != (double_speed ? 0x80u : 0u))
        { failure = 5; goto done; }
    for (size_t i = 0u; i < DMA_BYTES; ++i) {
        if (gbb_peek_ram(machine, 0xC200u + (uint16_t)i) != (uint8_t)(i ^ 0x5Au)) {
            data_match = 0;
            first_bad_byte = (int)i;
            break;
        }
    }
    if (out_data_match != NULL) *out_data_match = data_match;
    if (out_status_match != NULL) *out_status_match = status_match;
    if (out_timing_match != NULL) *out_timing_match = timing_match;
    if (!transfer_enabled)
        fprintf(stderr, "C consumer DMA disabled twin diagnosed: data=%d first_bad=%d status=%d timing=%d ff55=%02X calls=%u consumed=%llu\n",
                data_match, first_bad_byte, status_match, timing_match, gbb_peek_ram(machine, 0xC102u),
                calls, (unsigned long long)consumed);
    passed = transfer_enabled ? data_match && status_match && timing_match
                              : !data_match && !timing_match;

done:
    if (!passed && transfer_enabled)
        fprintf(stderr, "C consumer DMA guest failed: check=%d stop=%d marker=%02X ff55=%02X key1=%02X calls=%u consumed=%llu\n",
                failure, (int)last_reason,
                machine != NULL ? gbb_peek_ram(machine, 0xC103u) : 0u,
                machine != NULL ? gbb_peek_ram(machine, 0xC102u) : 0u,
                machine != NULL ? gbb_peek_ram(machine, 0xC104u) : 0u,
                calls, (unsigned long long)consumed);
    gbb_destroy(machine);
    return passed;
}

/* Installed-package RTC smoke: MBC3+TIMER+RAM+BATTERY ($10) synthetic ROM,
 * explicit host catch-up, block layout and a byte-identical import round trip. */
static void rtc_fill_rom(uint8_t *rom, size_t size, uint8_t cart_type) {
    memset(rom, 0, size);
    rom[0x100u] = 0xC3u; /* JP $0150 */
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x150u] = 0x76u; /* HALT */
    rom[0x151u] = 0x18u; /* JR -3 */
    rom[0x152u] = 0xFDu;
    rom[0x147u] = cart_type;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int rtc_api_smoke(void) {
    enum { ROM_BYTES = 32768, RAM_BYTES = 8192, IMAGE_BYTES = RAM_BYTES + GBB_RTC_BLOCK_SIZE };
    static uint8_t rom[ROM_BYTES];
    uint8_t first[IMAGE_BYTES];
    uint8_t second[IMAGE_BYTES];
    gbb_instance *machine = NULL;
    gbb_instance *twin = NULL;
    gbb_instance *plain = NULL;
    int passed = 0;

    rtc_fill_rom(rom, sizeof(rom), 0x10u);
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &twin) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK ||
        gbb_load_rom(twin, rom, sizeof(rom)) != GBB_OK) goto done;
    size_t size = 0u;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != IMAGE_BYTES) goto done;
    if (gbb_rtc_catch_up(machine, 3661) != GBB_OK) goto done;
    if (gbb_copy_battery(machine, first, sizeof(first)) != GBB_OK) goto done;
    if (first[RAM_BYTES] != 0x47u || first[RAM_BYTES + 1u] != 0x42u || /* "GB" */
        first[RAM_BYTES + 2u] != 0x52u || first[RAM_BYTES + 3u] != 0x54u) /* "RT" */
        goto done;
    if (first[RAM_BYTES + 9u] != 1u || first[RAM_BYTES + 10u] != 1u ||
        first[RAM_BYTES + 11u] != 1u) goto done;
    /* Import never catches up: the twin exports exactly the imported bytes. */
    if (gbb_import_battery(twin, first, sizeof(first)) != GBB_OK ||
        gbb_copy_battery(twin, second, sizeof(second)) != GBB_OK ||
        memcmp(first, second, sizeof(first)) != 0) goto done;
    if (gbb_rtc_catch_up(machine, -1) != GBB_INVALID_ARGUMENT) goto done;
    if (gbb_rtc_catch_up(NULL, 1) != GBB_INVALID_ARGUMENT) goto done;

    rtc_fill_rom(rom, sizeof(rom), 0x03u); /* MBC1+RAM+BATTERY: no timer */
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &plain) != GBB_OK ||
        gbb_load_rom(plain, rom, sizeof(rom)) != GBB_OK ||
        gbb_rtc_catch_up(plain, 1) != GBB_NO_RTC) goto done;
    passed = 1;

done:
    gbb_destroy(plain);
    gbb_destroy(twin);
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

// FNV-1a over little-endian left then right words, matching tests/test_audio.c.
static uint64_t fnv1a_frames(const gbb_audio_frame *frames, size_t count) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0u; i < count; ++i) {
        const uint16_t values[2] = {(uint16_t)(frames[i].left),
                                    (uint16_t)(frames[i].right)};
        for (unsigned channel = 0u; channel < 2u; ++channel) {
            hash ^= (uint8_t)(values[channel]);
            hash *= UINT64_C(1099511628211);
            hash ^= (uint8_t)(values[channel] >> 8);
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

// Structural PCM smoke through the installed public header and library only.
// Every assertion is a bound, a formula from header constants, or a comparison
// within this process; no emulator-derived digest or count is pinned.
static int audio_api_smoke(void) {
    enum { ROM_BYTES = 32768, CAPACITY = 804 };
    // Square-wave tracer: NR12 envelope, NR11 duty, NR13 period low, NR14 trigger, then JR -2.
    static const uint8_t program[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu,
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu,
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu,
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu,
        0x18u, 0xFEu
    };
    uint8_t rom[ROM_BYTES] = {0};
    memcpy(rom + 0x100u, program, sizeof(program));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    // 48000 Hz output over the 8388608 half-dot/s clock: one frame budget of
    // 140448 half-dots yields 803 PCM frames.
    const uint64_t budget = UINT64_C(140448);
    const size_t expected = (size_t)((budget * UINT64_C(48000)) / UINT64_C(8388608));
    const int16_t poison = (int16_t)0x7A5A;
    gbb_audio_frame frames[CAPACITY + 2u] = {{0, 0}};
    gbb_audio_frame twin_frames[CAPACITY + 2u] = {{0, 0}};
    gbb_instance *machine = NULL;
    gbb_instance *twin = NULL;
    gbb_instance *probe = NULL;
    size_t count = 0u;
    size_t twin_count = 0u;
    unsigned high_samples = 0u;
    unsigned transitions = 0u;
    uint64_t first_hash = 0u;
    gbb_run_result result = {0};
    gbb_run_result twin_result = {0};
    int passed = 0;

    for (size_t i = 0u; i < CAPACITY + 2u; ++i) {
        frames[i].left = frames[i].right = poison;
        twin_frames[i].left = twin_frames[i].right = poison;
    }
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &twin) != GBB_OK ||
        gbb_load_rom(twin, rom, sizeof(rom)) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &probe) != GBB_OK ||
        gbb_load_rom(probe, rom, sizeof(rom)) != GBB_OK) goto done;

    // (1) exact budget and formula frame count
    result = gbb_run_audio(machine, budget, frames, (size_t)CAPACITY, &count);
    if (!(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == budget &&
          count == expected)) goto done;
    // (2) activity bounds
    for (size_t i = 0u; i < count; ++i) {
        if (frames[i].left != frames[i].right) goto done;
        if (frames[i].left != 0) ++high_samples;
        if (i != 0u && frames[i].left != frames[i - 1u].left) ++transitions;
    }
    if (!(high_samples > 100u && high_samples < count && transitions > 20u)) goto done;
    // (3) poison past n, including the two guard frames beyond the capacity
    for (size_t i = count; i < CAPACITY + 2u; ++i)
        if (frames[i].left != poison || frames[i].right != poison) goto done;
    // (4) a second fresh instance matches
    twin_result = gbb_run_audio(twin, budget, twin_frames, (size_t)CAPACITY, &twin_count);
    if (!(twin_result.reason == result.reason &&
          twin_result.consumed_half_dots == result.consumed_half_dots &&
          twin_count == count)) goto done;
    first_hash = fnv1a_frames(frames, count);
    if (fnv1a_frames(twin_frames, twin_count) != first_hash) goto done;
    // (5) reset clears APU state, so a re-run reproduces the fresh-instance hash
    if (gbb_reset(machine) != GBB_OK) goto done;
    for (size_t i = 0u; i < CAPACITY + 2u; ++i)
        twin_frames[i].left = twin_frames[i].right = poison;
    twin_count = 0u;
    twin_result = gbb_run_audio(machine, budget, twin_frames, (size_t)CAPACITY, &twin_count);
    if (!(twin_result.reason == result.reason &&
          twin_result.consumed_half_dots == result.consumed_half_dots &&
          twin_count == count && fnv1a_frames(twin_frames, twin_count) == first_hash)) goto done;
    // (6) NULL frames with zero capacity stops before consuming the budget
    count = 1u;
    result = gbb_run_audio(probe, budget, NULL, 0u, &count);
    if (!(result.reason == GBB_STOP_OUTPUT_FULL && count == 0u &&
          result.consumed_half_dots < budget)) goto done;
    // (7) header-defined invalid shapes
    count = 1u;
    result = gbb_run_audio(probe, budget, NULL, 1u, &count);
    if (!(result.reason == GBB_STOP_INVALID_STATE && count == 0u)) goto done;
    result = gbb_run_audio(probe, budget, frames, (size_t)CAPACITY, NULL);
    if (result.reason != GBB_STOP_INVALID_STATE) goto done;
    count = 1u;
    result = gbb_run_audio(NULL, budget, frames, (size_t)CAPACITY, &count);
    if (!(result.reason == GBB_STOP_INVALID_STATE && count == 0u)) goto done;
    passed = 1;

done:
    gbb_destroy(machine);
    gbb_destroy(twin);
    gbb_destroy(probe);
    return passed ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (file == NULL || fseek(file, 0, SEEK_END) != 0) return 2;
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) return 2;
    uint8_t *rom = malloc((size_t)length);
    if (rom == NULL || fread(rom, 1, (size_t)length, file) != (size_t)length) return 2;
    fclose(file);

    gbb_instance *machine = NULL;
    gbb_error error = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine);
    if (error == GBB_OK) error = gbb_load_rom(machine, rom, (size_t)length);
    free(rom);
    gbb_input_event events[64];
    for (size_t i = 0; i < 64; ++i) {
        events[i].at_half_dots = i;
        events[i].kind = GBB_INPUT_STOP_WAKE;
        events[i].value = 1;
    }
    events[62] = (gbb_input_event){62, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    events[63] = (gbb_input_event){63, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A};
    gbb_error event_error = error == GBB_OK ? gbb_queue_events(machine, events, 64) : error;
    gbb_input_event excess = {64, (gbb_input_event_kind)99, 0};
    gbb_error capacity_error = event_error == GBB_OK ? gbb_queue_events(machine, &excess, 1) : event_error;
    gbb_trace_record *trace = calloc(16384, sizeof(*trace));
    gbb_diagnostic_record *diagnostics = calloc(16384, sizeof(*diagnostics));
    gbb_run_result result = {0};
    if (error == GBB_OK && event_error == GBB_OK && trace != NULL && diagnostics != NULL)
        result = gbb_run_ex(machine, UINT64_C(160000), trace, 16384, diagnostics, 16384);
    int chronological = 1;
    for (size_t i = 1; i < result.diagnostic_count; ++i)
        if (diagnostics[i - 1].time_half_dots > diagnostics[i].time_half_dots) chronological = 0;
    uint8_t frame[160u * 144u];
    gbb_frame_info frame_info = {0};
    gbb_error frame_error = error == GBB_OK
        ? gbb_copy_frame(machine, frame, sizeof(frame), 160, &frame_info) : error;
    int shades_valid = 1;
    if (frame_error == GBB_OK)
        for (size_t i = 0; i < sizeof(frame); ++i)
            if (frame[i] > 3u) shades_valid = 0;
    int passed = error == GBB_OK && event_error == GBB_OK && capacity_error == GBB_EVENT_QUEUE_FULL &&
        result.reason == GBB_STOP_BUDGET && result.consumed_half_dots <= UINT64_C(160000) &&
        trace != NULL && result.trace_count > 0 && result.trace_count <= 16384 &&
        diagnostics != NULL && result.diagnostic_count > 0 && result.diagnostic_count <= 16384 && chronological &&
        gbb_peek_ram(machine, 0xC001) == 0xA5 && frame_error == GBB_OK &&
        frame_info.width == 160 && frame_info.height == 144 && frame_info.generation > 0 && shades_valid;
    gbb_destroy(machine);
    free(trace);
    free(diagnostics);
    if (!passed) fprintf(stderr, "C consumer API smoke failed (error=%d, stop=%d, frame=%d)\n", error, result.reason, frame_error);
    if (!passed) {
        fprintf(stderr, "C consumer public core API smoke failed\n");
        return 1;
    }
    if (state_api_smoke() != 0) {
        fprintf(stderr, "C consumer public state API smoke failed\n");
        return 1;
    }
    if (battery_api_smoke() != 0) {
        fprintf(stderr, "C consumer public battery API smoke failed\n");
        return 1;
    }
    if (cgb_api_smoke() != 0) {
        fprintf(stderr, "C consumer public CGB API smoke failed\n");
        return 1;
    }
    {
        int unarmed_rejected = 0;
        if (!cgb_speed_partition_smoke(1u, NULL)) {
            fprintf(stderr, "C consumer CGB speed partition smoke failed\n");
            return 1;
        }
        if (cgb_speed_partition_smoke(0u, &unarmed_rejected) || !unarmed_rejected) {
            fprintf(stderr, "C consumer CGB speed smoke accepted unarmed twin\n");
            return 1;
        }
        printf("cgb_speed_partition_smoke unarmed twin rejected\n");
    }
    {
        int data_match = 0, status_match = 0, timing_match = 0;
        if (!cgb_dma_partition_smoke(0, 1, &data_match, &status_match, &timing_match)) {
            fprintf(stderr, "C consumer CGB DMA normal-speed guest predicate failed: data=%d status=%d timing=%d\n",
                    data_match, status_match, timing_match);
            return 1;
        }
        if (!cgb_dma_partition_smoke(1, 1, &data_match, &status_match, &timing_match)) {
            fprintf(stderr, "C consumer CGB DMA double-speed guest predicate failed: data=%d status=%d timing=%d\n",
                    data_match, status_match, timing_match);
            return 1;
        }
        /* FF55 reads FF both before a transfer and after GDMA completes; the
         * disabled twin must fail the data and CPU-steal timing predicates. */
        if (!cgb_dma_partition_smoke(0, 0, &data_match, &status_match, &timing_match) ||
            data_match || timing_match) {
            fprintf(stderr, "C consumer CGB DMA disabled twin lacked diagnosed mismatch\n");
            return 1;
        }
        printf("cgb_dma_partition_smoke disabled twin rejected: data=%d status=%d timing=%d\n",
               data_match, status_match, timing_match);
    }
    if (rtc_api_smoke() != 0) {
        fprintf(stderr, "C consumer public RTC API smoke failed\n");
        return 1;
    }
    if (audio_api_smoke() != 0) {
        fprintf(stderr, "C consumer public audio API smoke failed\n");
        return 1;
    }
    return 0;
}
