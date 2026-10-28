/* White-box save-state tests. This translation unit includes the real core so
 * it can seed and inspect lazy RTC state without exposing private fields. */
#ifndef GBB_CORE_SOURCE_PATH
#define GBB_CORE_SOURCE_PATH "../src/core/gabbaboy.c"
#endif
#define GBB_TEST_STATE_HASH_COUNTER 1
#include GBB_CORE_SOURCE_PATH

#include <stdio.h>
#include <stdlib.h>

#define REQUIRE_CASE(name, condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", (name), __LINE__, #condition); \
        return 1; \
    } \
} while (0)

#define TEST_ROM_BYTES 0x8000u
#define TEST_STATE_HEADER_BYTES 64u
#define RTC_HALF_DOTS_PER_SECOND (UINT64_C(1) << 23)

static void fix_header_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0u; i < 0x19u; ++i)
        checksum = (uint8_t)(checksum - rom[0x134u + i] - 1u);
    rom[0x14Du] = checksum;
}

static void build_rom(uint8_t rom[TEST_ROM_BYTES], uint8_t type, uint8_t cgb_flag) {
    memset(rom, 0, TEST_ROM_BYTES);
    static const uint8_t audio_loop[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu,
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu,
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu,
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu,
        0x18u, 0xFEu
    };
    rom[0x143u] = cgb_flag;
    rom[0x147u] = type;
    rom[0x148u] = 0u;
    rom[0x149u] = (type == 0x10u || type == 0x1Eu) ? 0x02u : 0u;
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, audio_loop, sizeof(audio_loop));
    fix_header_checksum(rom);
}

static gbb_instance *new_machine(const uint8_t rom[TEST_ROM_BYTES], gbb_profile profile) {
    gbb_instance *machine = NULL;
    if (gbb_create(profile, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, TEST_ROM_BYTES) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static void set_palette(gbb_compat_palette *palette, uint16_t seed) {
    palette->struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    for (size_t i = 0u; i < 4u; ++i) {
        palette->bg[i] = (uint16_t)(seed + i * 3u);
        palette->obj0[i] = (uint16_t)(seed + 0x100u + i * 5u);
        palette->obj1[i] = (uint16_t)(seed + 0x200u + i * 7u);
    }
}

static int same_palette(const gbb_compat_palette *a, const gbb_compat_palette *b) {
    return memcmp(a->bg, b->bg, sizeof(a->bg)) == 0 &&
           memcmp(a->obj0, b->obj0, sizeof(a->obj0)) == 0 &&
           memcmp(a->obj1, b->obj1, sizeof(a->obj1)) == 0;
}

static void fill_ram(gbb_instance *machine, uint8_t seed) {
    for (size_t i = 0u; i < machine->cartridge_ram_size; ++i)
        machine->cartridge_ram[i] = (uint8_t)(seed + i * 29u);
}

static void seed_rtc(gbb_instance *machine, uint8_t seconds, uint32_t sub,
                     uint64_t anchor) {
    machine->cart.rtc_s = seconds;
    machine->cart.rtc_m = 34u;
    machine->cart.rtc_h = 12u;
    machine->cart.rtc_dl = 0xA5u;
    machine->cart.rtc_dh = 0x81u;
    machine->cart.rtc_l[0] = 9u;
    machine->cart.rtc_l[1] = 10u;
    machine->cart.rtc_l[2] = 3u;
    machine->cart.rtc_l[3] = 0x44u;
    machine->cart.rtc_l[4] = 0x80u;
    machine->cart.rtc_latch_prev = 0u;
    machine->cart.rtc_sub = sub;
    machine->cart.rtc_synced_at = anchor;
}

static int same_rtc(const cart_state *a, const cart_state *b) {
    return a->rtc_s == b->rtc_s && a->rtc_m == b->rtc_m && a->rtc_h == b->rtc_h &&
           a->rtc_dl == b->rtc_dl && a->rtc_dh == b->rtc_dh &&
           memcmp(a->rtc_l, b->rtc_l, sizeof(a->rtc_l)) == 0 &&
           a->rtc_latch_prev == b->rtc_latch_prev && a->rtc_sub == b->rtc_sub &&
           a->rtc_synced_at == b->rtc_synced_at;
}

static int same_run(gbb_run_result a, gbb_run_result b) {
    return a.consumed_half_dots == b.consumed_half_dots && a.reason == b.reason &&
           a.trace_count == b.trace_count && a.diagnostic_count == b.diagnostic_count &&
           a.lockup_pc == b.lockup_pc && a.lockup_opcode == b.lockup_opcode;
}

static int same_frame(gbb_frame_info a, gbb_frame_info b) {
    return a.width == b.width && a.height == b.height && a.generation == b.generation &&
           a.completion_half_dots == b.completion_half_dots;
}

static int state_rtc_palette(void) {
    const char *case_name = "state_rtc_palette";
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x10u, 0u); /* MBC3 timer + battery RAM, CGB compatibility mode. */
    gbb_instance *source = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(case_name, source != NULL && target != NULL);
    REQUIRE_CASE(case_name, source->exec_mode == GBB_MODE_CGB_DMG_COMPAT &&
                            target->exec_mode == GBB_MODE_CGB_DMG_COMPAT);

    gbb_audio_frame prefix[1024];
    size_t prefix_count = 0u;
    const gbb_run_result prefix_run = gbb_run_audio(source, 70000u, prefix, 1024u,
                                                     &prefix_count);
    REQUIRE_CASE(case_name, prefix_run.reason == GBB_STOP_BUDGET && prefix_count != 0u);
    const gbb_run_result poison_run = gbb_run(target, 23000u, NULL, 0u);
    REQUIRE_CASE(case_name, poison_run.reason == GBB_STOP_BUDGET);

    gbb_compat_palette source_palette = {0}, target_palette = {0};
    set_palette(&source_palette, 0x011u);
    set_palette(&target_palette, 0x411u);
    REQUIRE_CASE(case_name, gbb_set_compat_palette(source, &source_palette) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_set_compat_palette(target, &target_palette) == GBB_OK);
    fill_ram(source, 0x31u);
    fill_ram(target, 0xC7u);
    seed_rtc(source, 58u, RTC_SUB_MASK - 10u, source->time_half_dots - 5u);
    seed_rtc(target, 3u, 77u, target->time_half_dots - 1u);

    target->battery_generation = 41u;
    target->cart.rumble_changes = 89u;
    source->battery_generation = 7u;
    source->cart.rumble_changes = 13u;
    size_t state_size = 0u;
    REQUIRE_CASE(case_name, gbb_state_size(source, &state_size) == GBB_OK);
    uint8_t *saved = malloc(state_size + 1u);
    uint8_t *resaved = malloc(state_size + 1u);
    REQUIRE_CASE(case_name, saved != NULL && resaved != NULL);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, state_size) == GBB_OK);
    const uint64_t hash_calls = state_sha256_test_calls;
    REQUIRE_CASE(case_name, gbb_load_state(target, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, state_sha256_test_calls == hash_calls);
    REQUIRE_CASE(case_name, same_rtc(&source->cart, &target->cart));
    REQUIRE_CASE(case_name, memcmp(source->cartridge_ram, target->cartridge_ram,
                                   source->cartridge_ram_size) == 0);
    REQUIRE_CASE(case_name, target->battery_generation == 42u);
    REQUIRE_CASE(case_name, target->cart.rumble_changes == 89u);
    gbb_compat_palette observed_palette = {.struct_size = GBB_COMPAT_PALETTE_SIZE_V1};
    REQUIRE_CASE(case_name, gbb_get_compat_palette(target, &observed_palette) == GBB_OK);
    REQUIRE_CASE(case_name, same_palette(&source_palette, &observed_palette));
    REQUIRE_CASE(case_name, gbb_save_state(target, resaved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, memcmp(saved, resaved, state_size) == 0);

    size_t battery_size = 0u;
    REQUIRE_CASE(case_name, gbb_battery_size(source, &battery_size) == GBB_OK);
    REQUIRE_CASE(case_name, battery_size == 8192u + GBB_RTC_BLOCK_SIZE);
    uint8_t *source_battery = malloc(battery_size);
    uint8_t *target_battery = malloc(battery_size);
    REQUIRE_CASE(case_name, source_battery != NULL && target_battery != NULL);
    REQUIRE_CASE(case_name, gbb_copy_battery(source, source_battery, battery_size) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_copy_battery(target, target_battery, battery_size) == GBB_OK);
    REQUIRE_CASE(case_name, memcmp(source_battery, target_battery, battery_size) == 0);

    gbb_audio_frame source_audio[1024], target_audio[1024];
    size_t source_audio_count = 0u, target_audio_count = 0u;
    const gbb_run_result source_future = gbb_run_audio(source, 140448u, source_audio,
                                                        1024u, &source_audio_count);
    const gbb_run_result target_future = gbb_run_audio(target, 140448u, target_audio,
                                                        1024u, &target_audio_count);
    REQUIRE_CASE(case_name, same_run(source_future, target_future));
    REQUIRE_CASE(case_name, source_audio_count == target_audio_count);
    REQUIRE_CASE(case_name, memcmp(source_audio, target_audio,
                                   source_audio_count * sizeof(source_audio[0])) == 0);

    uint16_t source_pixels[GBB_FRAME_PIXELS], target_pixels[GBB_FRAME_PIXELS];
    gbb_frame_info source_info = {0}, target_info = {0};
    REQUIRE_CASE(case_name, gbb_copy_frame_rgb555(source, source_pixels, sizeof(source_pixels),
        GBB_FRAME_WIDTH * sizeof(uint16_t), &source_info) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_copy_frame_rgb555(target, target_pixels, sizeof(target_pixels),
        GBB_FRAME_WIDTH * sizeof(uint16_t), &target_info) == GBB_OK);
    REQUIRE_CASE(case_name, same_frame(source_info, target_info));
    REQUIRE_CASE(case_name, memcmp(source_pixels, target_pixels, sizeof(source_pixels)) == 0);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_save_state(target, resaved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, memcmp(saved, resaved, state_size) == 0);
    REQUIRE_CASE(case_name, state_sha256_test_calls == hash_calls);

    free(target_battery);
    free(source_battery);
    free(resaved);
    free(saved);
    gbb_destroy(target);
    gbb_destroy(source);
    puts("state_rtc_palette pass raw_rtc=exact palette=restored battery=canonical continuation=equal");
    return 0;
}

static int state_observers(void) {
    const char *case_name = "state_observers";
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x10u, 0u);
    gbb_instance *source = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target_a = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target_b = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(case_name, source != NULL && target_a != NULL && target_b != NULL);
    fill_ram(source, 0x24u);
    seed_rtc(source, 1u, 0u, 0u);
    source->time_half_dots = 0u;
    source->battery_generation = 9u;
    source->cart.rumble_changes = 17u;
    size_t state_size = 0u;
    REQUIRE_CASE(case_name, gbb_state_size(source, &state_size) == GBB_OK);
    uint8_t *saved = malloc(state_size);
    uint8_t *counter_variant = malloc(state_size);
    REQUIRE_CASE(case_name, saved != NULL && counter_variant != NULL);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, state_size) == GBB_OK);
    source->battery_generation = 0x1234u;
    source->cart.rumble_changes = 0x5678u;
    REQUIRE_CASE(case_name, gbb_save_state(source, counter_variant, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, memcmp(saved, counter_variant, state_size) == 0);

    memcpy(target_a->cartridge_ram, source->cartridge_ram, source->cartridge_ram_size);
    target_a->time_half_dots = RTC_HALF_DOTS_PER_SECOND;
    seed_rtc(target_a, 0u, 0u, 0u);
    target_a->cart.rtc_m = 34u;
    target_a->cart.rtc_h = 12u;
    target_a->cart.rtc_dl = 0xA5u;
    target_a->cart.rtc_dh = 0x81u;
    target_a->cart.rtc_l[0] = 9u;
    target_a->cart.rtc_l[1] = 10u;
    target_a->cart.rtc_l[2] = 3u;
    target_a->cart.rtc_l[3] = 0x44u;
    target_a->cart.rtc_l[4] = 0x80u;
    target_a->cart.rtc_latch_prev = 0u;
    target_a->battery_generation = 7u;
    target_a->cart.rumble_changes = 31u;
    /* The target's lazy representation differs, but its RTC battery image at its
     * own emulated time equals the saved image at the source's time. */
    REQUIRE_CASE(case_name, gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_a->battery_generation == 7u);
    REQUIRE_CASE(case_name, target_a->cart.rumble_changes == 31u);
    REQUIRE_CASE(case_name, same_rtc(&source->cart, &target_a->cart));

    target_a->cart.rtc_s = 2u;
    target_a->battery_generation = 7u;
    REQUIRE_CASE(case_name, gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_a->battery_generation == 8u);
    REQUIRE_CASE(case_name, gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_a->battery_generation == 8u);

    target_a->cartridge_ram[17] ^= 0xFFu;
    REQUIRE_CASE(case_name, gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_a->battery_generation == 9u);
    REQUIRE_CASE(case_name, gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_a->battery_generation == 9u);

    target_a->cartridge_ram[17] ^= 0xFFu;
    target_a->battery_generation = UINT64_MAX;
    REQUIRE_CASE(case_name, gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_a->battery_generation == UINT64_MAX);

    fill_ram(target_b, 0xD2u);
    target_b->battery_generation = 100u;
    target_b->cart.rumble_changes = 200u;
    REQUIRE_CASE(case_name, gbb_load_state(target_b, saved, state_size) == GBB_OK);
    REQUIRE_CASE(case_name, target_b->battery_generation == 101u);
    REQUIRE_CASE(case_name, target_b->cart.rumble_changes == 200u);
    REQUIRE_CASE(case_name, target_a->battery_generation == UINT64_MAX);

    build_rom(rom, 0x1Eu, 0x80u); /* MBC5 battery RAM + rumble line. */
    gbb_instance *rumble_source = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *rumble_a = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *rumble_b = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(case_name, rumble_source != NULL && rumble_a != NULL && rumble_b != NULL);
    rumble_source->cart.rumble_on = 1u;
    rumble_source->cart.rumble_changes = 3u;
    size_t rumble_size = 0u;
    REQUIRE_CASE(case_name, gbb_state_size(rumble_source, &rumble_size) == GBB_OK);
    uint8_t *rumble_saved = malloc(rumble_size);
    uint8_t *rumble_variant = malloc(rumble_size);
    REQUIRE_CASE(case_name, rumble_saved != NULL && rumble_variant != NULL);
    REQUIRE_CASE(case_name, gbb_save_state(rumble_source, rumble_saved, rumble_size) == GBB_OK);
    rumble_source->cart.rumble_changes = UINT64_MAX;
    REQUIRE_CASE(case_name, gbb_save_state(rumble_source, rumble_variant, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, memcmp(rumble_saved, rumble_variant, rumble_size) == 0);

    rumble_a->cart.rumble_changes = 5u;
    rumble_b->cart.rumble_changes = 99u;
    REQUIRE_CASE(case_name, gbb_load_state(rumble_a, rumble_saved, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_load_state(rumble_b, rumble_saved, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, rumble_a->cart.rumble_on == 1u && rumble_a->cart.rumble_changes == 6u);
    REQUIRE_CASE(case_name, rumble_b->cart.rumble_on == 1u && rumble_b->cart.rumble_changes == 100u);
    REQUIRE_CASE(case_name, gbb_load_state(rumble_a, rumble_saved, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, rumble_a->cart.rumble_changes == 6u);
    rumble_a->cart.rumble_changes = UINT64_MAX;
    rumble_a->cart.rumble_on = 0u;
    REQUIRE_CASE(case_name, gbb_load_state(rumble_a, rumble_saved, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, rumble_a->cart.rumble_changes == UINT64_MAX);

    rumble_source->cart.rumble_on = 0u;
    REQUIRE_CASE(case_name, gbb_save_state(rumble_source, rumble_saved, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_load_state(rumble_b, rumble_saved, rumble_size) == GBB_OK);
    REQUIRE_CASE(case_name, rumble_b->cart.rumble_on == 0u && rumble_b->cart.rumble_changes == 101u);

    free(rumble_variant);
    free(rumble_saved);
    gbb_destroy(rumble_b);
    gbb_destroy(rumble_a);
    gbb_destroy(rumble_source);
    free(counter_variant);
    free(saved);
    gbb_destroy(target_b);
    gbb_destroy(target_a);
    gbb_destroy(source);
    puts("state_observers pass projected_equal=0 changed=1 repeat=0 rumble_local=saturated-safe");
    return 0;
}

typedef struct {
    gbb_instance raw;
    uint8_t *rom;
    uint8_t *ram;
} state_instance_snapshot;

static int state_snapshot_init(state_instance_snapshot *snapshot,
                               const gbb_instance *instance) {
    memset(snapshot, 0, sizeof(*snapshot));
    snapshot->rom = instance->rom_size == 0u ? NULL : malloc(instance->rom_size);
    snapshot->ram = instance->cartridge_ram_size == 0u ? NULL :
                    malloc(instance->cartridge_ram_size);
    if ((instance->rom_size != 0u && snapshot->rom == NULL) ||
        (instance->cartridge_ram_size != 0u && snapshot->ram == NULL)) {
        free(snapshot->rom);
        free(snapshot->ram);
        memset(snapshot, 0, sizeof(*snapshot));
        return 0;
    }
    return 1;
}

static void state_snapshot_capture(state_instance_snapshot *snapshot,
                                   const gbb_instance *instance) {
    memcpy(&snapshot->raw, instance, sizeof(*instance));
    if (instance->rom_size != 0u) memcpy(snapshot->rom, instance->rom, instance->rom_size);
    if (instance->cartridge_ram_size != 0u)
        memcpy(snapshot->ram, instance->cartridge_ram, instance->cartridge_ram_size);
}

static int state_snapshot_matches(const state_instance_snapshot *snapshot,
                                  const gbb_instance *instance) {
    return memcmp(&snapshot->raw, instance, sizeof(*instance)) == 0 &&
           (instance->rom_size == 0u ||
            memcmp(snapshot->rom, instance->rom, instance->rom_size) == 0) &&
           (instance->cartridge_ram_size == 0u ||
            memcmp(snapshot->ram, instance->cartridge_ram,
                   instance->cartridge_ram_size) == 0);
}

static void state_internal_rechecksum(uint8_t *state, size_t total_size) {
    uint32_t crc = state_crc32_update(UINT32_MAX, state, 60u);
    crc = state_crc32_update(crc, state + TEST_STATE_HEADER_BYTES,
                             total_size - TEST_STATE_HEADER_BYTES) ^ UINT32_MAX;
    state_put_u32(state + 60u, crc);
}

static int state_internal_write_field(const gbb_instance *instance, uint8_t *state,
                                      const char *path, uint64_t value) {
    const state_field_descriptor *field = state_field_by_path(path);
    if (field == NULL || field->wire_width > 8u) return 0;
    const size_t offset = state_body_field_offset(instance, field);
    if (offset == SIZE_MAX || offset > SIZE_MAX - TEST_STATE_HEADER_BYTES) return 0;
    state_put_u64(state + TEST_STATE_HEADER_BYTES + offset, value, field->wire_width);
    return 1;
}

static void state_snapshot_destroy(state_instance_snapshot *snapshot) {
    free(snapshot->rom);
    free(snapshot->ram);
    memset(snapshot, 0, sizeof(*snapshot));
}

static int state_expect_refusal(state_instance_snapshot *snapshot,
                                gbb_instance *instance, const uint8_t *bytes,
                                size_t size, gbb_error expected) {
    if (instance == NULL)
        return gbb_load_state(instance, bytes, size) == expected;
    state_snapshot_capture(snapshot, instance);
    const gbb_error got = gbb_load_state(instance, bytes, size);
    const int unchanged = state_snapshot_matches(snapshot, instance);
    if (got != expected || !unchanged) {
        fprintf(stderr, "state refusal got=%d expected=%d unchanged=%d size=%zu\n",
                (int)got, (int)expected, unchanged, size);
        return 0;
    }
    return 1;
}

static int state_expect_refusal_unchanged(const state_instance_snapshot *snapshot,
                                          gbb_instance *instance,
                                          const uint8_t *bytes, size_t size,
                                          gbb_error expected) {
    const gbb_error got = gbb_load_state(instance, bytes, size);
    const int unchanged = state_snapshot_matches(snapshot, instance);
    if (got != expected || !unchanged) {
        fprintf(stderr, "state refusal got=%d expected=%d unchanged=%d size=%zu\n",
                (int)got, (int)expected, unchanged, size);
        return 0;
    }
    return 1;
}

static int state_refusal_controls(void) {
    const char *case_name = "state_refusal_controls";
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x10u, 0u);
    gbb_instance *target = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(case_name, target != NULL && target->cartridge_ram_size != 0u);
    state_instance_snapshot snapshot;
    REQUIRE_CASE(case_name, state_snapshot_init(&snapshot, target));
    state_snapshot_capture(&snapshot, target);
    target->battery_generation ^= UINT64_C(1);
    REQUIRE_CASE(case_name, !state_snapshot_matches(&snapshot, target));
    memcpy(target, &snapshot.raw, sizeof(*target));
    target->cartridge_ram[0] ^= 1u;
    REQUIRE_CASE(case_name, !state_snapshot_matches(&snapshot, target));
    memcpy(target, &snapshot.raw, sizeof(*target));
    memcpy(target->cartridge_ram, snapshot.ram, target->cartridge_ram_size);
    REQUIRE_CASE(case_name, state_snapshot_matches(&snapshot, target));
    state_snapshot_destroy(&snapshot);
    gbb_destroy(target);
    puts("state_refusal_controls pass instance_and_owned_ram_sensitive");
    return 0;
}

static int state_refusal(void) {
    const char *case_name = "state_refusal";
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x10u, 0u);
    gbb_instance *source = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *empty = NULL;
    REQUIRE_CASE(case_name, source != NULL && target != NULL);
    REQUIRE_CASE(case_name, gbb_create(GBB_PROFILE_CGB_CPU_E, &empty) == GBB_OK);
    fill_ram(target, 0xD3u);
    target->battery_generation = 0x1020304050607080u;
    target->cart.rumble_changes = 0x8877665544332211u;
    state_instance_snapshot snapshot;
    state_instance_snapshot empty_snapshot;
    REQUIRE_CASE(case_name, state_snapshot_init(&snapshot, target));
    REQUIRE_CASE(case_name, state_snapshot_init(&empty_snapshot, empty));
    size_t size = 0u;
    REQUIRE_CASE(case_name, gbb_state_size(source, &size) == GBB_OK);
    uint8_t *saved = malloc(size + 1u);
    uint8_t *mutant = malloc(size + 1u);
    REQUIRE_CASE(case_name, saved != NULL && mutant != NULL);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, size) == GBB_OK);

    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, NULL, saved, size,
                                                  GBB_INVALID_ARGUMENT));
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, NULL, size,
                                                  GBB_INVALID_ARGUMENT));
    state_snapshot_capture(&snapshot, target);
    for (size_t truncated = 0u; truncated < size; ++truncated) {
        const gbb_error expected = truncated < TEST_STATE_HEADER_BYTES ?
                                   GBB_STATE_BAD_FORMAT : GBB_STATE_SIZE_MISMATCH;
        REQUIRE_CASE(case_name, state_expect_refusal_unchanged(&snapshot, target, saved,
                                                                truncated, expected));
    }

    memcpy(mutant, saved, size);
    mutant[0] ^= 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_BAD_FORMAT));
    static const size_t version_offsets[] = {4u, 6u, 8u, 10u, 12u, 14u};
    for (size_t i = 0u; i < sizeof(version_offsets) / sizeof(version_offsets[0]); ++i) {
        memcpy(mutant, saved, size);
        const size_t offset = version_offsets[i];
        state_put_u16(mutant + offset,
                      (uint16_t)(state_get_u16(mutant + offset) + 1u));
        REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                      GBB_STATE_UNSUPPORTED_VERSION));
    }
    memcpy(mutant, saved, size);
    mutant[16] = GBB_PROFILE_DMG_CPU_B;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_IDENTITY_MISMATCH));
    memcpy(mutant, saved, size);
    mutant[17] = GBB_MODE_CGB;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_IDENTITY_MISMATCH));
    /* Magic precedes version; version precedes no-ROM. */
    memcpy(mutant, saved, size);
    state_put_u16(mutant + 4u, (uint16_t)(GBB_STATE_FORMAT_VERSION + 1u));
    REQUIRE_CASE(case_name, state_expect_refusal(&empty_snapshot, empty, mutant, size,
                                                  GBB_STATE_UNSUPPORTED_VERSION));
    REQUIRE_CASE(case_name, state_expect_refusal(&empty_snapshot, empty, saved, size,
                                                  GBB_STATE_NO_ROM));
    memcpy(mutant, saved, size);
    mutant[20] ^= 1u;
    state_put_u32(mutant + 52u, 0u);
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_IDENTITY_MISMATCH));

    /* A correct-identity state with a wrong declared or supplied length is
     * rejected before checksum and semantic content are consulted. */
    memcpy(mutant, saved, size);
    state_put_u32(mutant + 56u, (uint32_t)(size + 1u));
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_SIZE_MISMATCH));
    memcpy(mutant, saved, size);
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size - 1u,
                                                  GBB_STATE_SIZE_MISMATCH));
    memcpy(mutant, saved, size);
    mutant[size] = 0xA7u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size + 1u,
                                                  GBB_STATE_SIZE_MISMATCH));

    memcpy(mutant, saved, size);
    mutant[TEST_STATE_HEADER_BYTES + 1u] ^= 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_CORRUPT));
    memcpy(mutant, saved, size);
    mutant[18] = 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_CORRUPT));
    memcpy(mutant, saved, size);
    mutant[18] = 1u;
    state_internal_rechecksum(mutant, size);
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_INVALID_CONTENT));
    /* A CRC-valid relationship violation complements the range-domain checks. */
    memcpy(mutant, saved, size);
    REQUIRE_CASE(case_name, state_internal_write_field(target, mutant,
                                                       "timer_reload_pending", 1u));
    REQUIRE_CASE(case_name, state_internal_write_field(target, mutant,
                                                       "timer_reload_remaining", 0u));
    state_internal_rechecksum(mutant, size);
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_INVALID_CONTENT));
    /* CRC-valid boolean-domain failure is late enough to catch apply-first. */
    memcpy(mutant, saved, size);
    REQUIRE_CASE(case_name, state_internal_write_field(target, mutant, "cart.ram_enabled", 2u));
    state_internal_rechecksum(mutant, size);
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_INVALID_CONTENT));
    /* CRC failure wins over that same invalid body; content follows CRC. */
    mutant[60] ^= 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_CORRUPT));

    /* Compound precedence edges independently exercise format, no-ROM,
     * identity, size, CRC and semantic validation. */
    memcpy(mutant, saved, size);
    mutant[0] = 'X';
    state_put_u16(mutant + 4u, (uint16_t)(GBB_STATE_FORMAT_VERSION + 1u));
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_BAD_FORMAT));
    memcpy(mutant, saved, size);
    state_put_u16(mutant + 4u, (uint16_t)(GBB_STATE_FORMAT_VERSION + 1u));
    state_put_u32(mutant + 52u, 0u);
    REQUIRE_CASE(case_name, state_expect_refusal(&empty_snapshot, empty, mutant, size,
                                                  GBB_STATE_UNSUPPORTED_VERSION));
    memcpy(mutant, saved, size);
    mutant[20] ^= 1u;
    mutant[TEST_STATE_HEADER_BYTES] ^= 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_IDENTITY_MISMATCH));
    memcpy(mutant, saved, size);
    state_put_u32(mutant + 56u, (uint32_t)(size + 7u));
    mutant[18] = 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_SIZE_MISMATCH));
    memcpy(mutant, saved, size);
    mutant[18] = 1u;
    mutant[TEST_STATE_HEADER_BYTES] ^= 1u;
    REQUIRE_CASE(case_name, state_expect_refusal(&snapshot, target, mutant, size,
                                                  GBB_STATE_CORRUPT));

    /* Error paths preserve poisoned size output and every output byte. */
    size_t poisoned_size = SIZE_MAX - 11u;
    state_snapshot_capture(&snapshot, target);
    REQUIRE_CASE(case_name, gbb_state_size(target, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE_CASE(case_name, state_snapshot_matches(&snapshot, target));
    REQUIRE_CASE(case_name, gbb_state_size(NULL, &poisoned_size) == GBB_INVALID_ARGUMENT &&
                            poisoned_size == SIZE_MAX - 11u);
    REQUIRE_CASE(case_name, gbb_state_size(empty, &poisoned_size) == GBB_STATE_NO_ROM &&
                            poisoned_size == SIZE_MAX - 11u);
    uint8_t *out = malloc(size + 16u);
    REQUIRE_CASE(case_name, out != NULL);
    memset(out, 0x5Au, size + 16u);
    state_snapshot_capture(&snapshot, target);
    REQUIRE_CASE(case_name, gbb_save_state(target, out, size - 1u) == GBB_BUFFER_TOO_SMALL);
    REQUIRE_CASE(case_name, state_snapshot_matches(&snapshot, target));
    for (size_t i = 0u; i < size + 16u; ++i)
        REQUIRE_CASE(case_name, out[i] == 0x5Au);
    REQUIRE_CASE(case_name, gbb_save_state(target, NULL, size) == GBB_INVALID_ARGUMENT);
    REQUIRE_CASE(case_name, gbb_save_state(NULL, out, size) == GBB_INVALID_ARGUMENT);
    REQUIRE_CASE(case_name, gbb_save_state(empty, out, size + 16u) == GBB_STATE_NO_ROM);
    for (size_t i = 0u; i < size + 16u; ++i)
        REQUIRE_CASE(case_name, out[i] == 0x5Au);
    REQUIRE_CASE(case_name, gbb_save_state(target, out, size + 16u) == GBB_OK);
    for (size_t i = size; i < size + 16u; ++i)
        REQUIRE_CASE(case_name, out[i] == 0x5Au);

    free(out);
    free(mutant);
    free(saved);
    state_snapshot_destroy(&empty_snapshot);
    state_snapshot_destroy(&snapshot);
    gbb_destroy(empty);
    gbb_destroy(target);
    gbb_destroy(source);
    puts("state_refusal pass precedence=ordered whole_instance_ram=unchanged output=bounded");
    return 0;
}

static int state_apu_pulse_timer(void) {
    const char *case_name = "state_apu_pulse_timer";
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x00u, 0u);
    gbb_instance *source = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(case_name, source != NULL && target != NULL);

    reset_state(source);
    REQUIRE_CASE(case_name, source->apu_pulse[0].timer <= GBB_APU_PULSE_TIMER_MAX &&
                            source->apu_pulse[1].timer <= GBB_APU_PULSE_TIMER_MAX);
    source->apu_power = 1u;
    source->apu_pulse[0].envelope = 0xF0u;
    uint16_t maximum_reload = 0u;
    for (uint16_t frequency = 0u; frequency <= 2047u; ++frequency) {
        source->apu_pulse[0].frequency_low = (uint8_t)frequency;
        source->apu_pulse[0].control = (uint8_t)((frequency >> 8) & 7u);
        apu_pulse_trigger(source, 0u);
        if (source->apu_pulse[0].timer > maximum_reload)
            maximum_reload = source->apu_pulse[0].timer;
        REQUIRE_CASE(case_name, source->apu_pulse[0].timer <= GBB_APU_PULSE_TIMER_MAX);
    }
    REQUIRE_CASE(case_name, maximum_reload == GBB_APU_PULSE_TIMER_MAX);

    /* Sweep's in-range result 1025 reaches the same maximum reload path. */
    apu_pulse_channel *pulse = &source->apu_pulse[0];
    pulse->frequency = 820u;
    pulse->frequency_low = (uint8_t)820u;
    pulse->control = (uint8_t)(820u >> 8);
    pulse->sweep = 0x22u;
    pulse->sweep_shadow = 820u;
    pulse->sweep_enabled = 1;
    pulse->sweep_timer = 1u;
    source->apu_sequencer_step = 2u;
    apu_sequencer_clock(source);
    REQUIRE_CASE(case_name, pulse->frequency == 1025u &&
                            pulse->timer == GBB_APU_PULSE_TIMER_MAX);

    source->apu_power = 0u;
    apu_power_off(source);
    REQUIRE_CASE(case_name, source->apu_pulse[0].timer == 0u &&
                            source->apu_pulse[1].timer == 0u);
    source->apu_power = 1u;
    source->apu_pulse[0].envelope = 0xF0u;
    source->apu_pulse[0].frequency_low = 1u;
    source->apu_pulse[0].control = 4u;
    apu_pulse_trigger(source, 0u);
    REQUIRE_CASE(case_name, source->apu_pulse[0].frequency == 1025u &&
                            source->apu_pulse[0].timer == GBB_APU_PULSE_TIMER_MAX);
    size_t size = 0u;
    REQUIRE_CASE(case_name, gbb_state_size(source, &size) == GBB_OK);
    const state_field_descriptor *timer_field = state_field_by_path("apu_pulse[].timer");
    REQUIRE_CASE(case_name, timer_field != NULL &&
                            state_field_value_valid(source, timer_field, 0u,
                                GBB_APU_PULSE_TIMER_MAX,
                                source->audio_event_head, source->apu_sample_phase, NULL) &&
                            !state_field_value_valid(source, timer_field, 0u,
                                GBB_APU_PULSE_TIMER_MAX + 1u,
                                source->audio_event_head, source->apu_sample_phase, NULL));
    uint8_t *saved = malloc(size);
    uint8_t *resaved = malloc(size);
    uint8_t *above_bound = malloc(size);
    REQUIRE_CASE(case_name, saved != NULL && resaved != NULL && above_bound != NULL);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_load_state(target, saved, size) == GBB_OK);
    REQUIRE_CASE(case_name, target->apu_pulse[0].timer == GBB_APU_PULSE_TIMER_MAX);
    REQUIRE_CASE(case_name, gbb_save_state(target, resaved, size) == GBB_OK &&
                            memcmp(saved, resaved, size) == 0);

    gbb_audio_frame source_audio[1024], target_audio[1024];
    size_t source_count = 0u, target_count = 0u;
    const gbb_run_result source_run = gbb_run_audio(source, 140448u, source_audio,
                                                     1024u, &source_count);
    const gbb_run_result target_run = gbb_run_audio(target, 140448u, target_audio,
                                                     1024u, &target_count);
    REQUIRE_CASE(case_name, source_run.reason == GBB_STOP_BUDGET &&
                            same_run(source_run, target_run));
    REQUIRE_CASE(case_name, source_count == target_count &&
                            memcmp(source_audio, target_audio,
                                   source_count * sizeof(source_audio[0])) == 0);
    REQUIRE_CASE(case_name, source->apu_pulse[0].timer < GBB_APU_PULSE_TIMER_MAX &&
                            source->apu_pulse[0].timer <= GBB_APU_PULSE_TIMER_MAX &&
                            target->apu_pulse[0].timer == source->apu_pulse[0].timer);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, size) == GBB_OK &&
                            gbb_save_state(target, resaved, size) == GBB_OK &&
                            memcmp(saved, resaved, size) == 0);

    memcpy(above_bound, saved, size);
    REQUIRE_CASE(case_name, state_internal_write_field(target, above_bound,
                                                       "apu_pulse[].timer",
                                                       GBB_APU_PULSE_TIMER_MAX + 1u));
    state_internal_rechecksum(above_bound, size);
    state_instance_snapshot snapshot;
    REQUIRE_CASE(case_name, state_snapshot_init(&snapshot, target));
    target->apu_pulse[0].timer = 1234u;
    state_snapshot_capture(&snapshot, target);
    REQUIRE_CASE(case_name, state_expect_refusal_unchanged(&snapshot, target,
        above_bound, size, GBB_STATE_INVALID_CONTENT));

    state_snapshot_destroy(&snapshot);
    free(above_bound);
    free(resaved);
    free(saved);
    gbb_destroy(target);
    gbb_destroy(source);
    puts("state_apu_pulse_timer pass reload_max=65472 roundtrip=continuation-equal above_bound=crc-valid-refused unchanged=1");
    return 0;
}

static int state_apu_noise_timer(void) {
    const char *case_name = "state_apu_noise_timer";
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x00u, 0u);
    gbb_instance *source = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(case_name, source != NULL && target != NULL);

    reset_state(source);
    REQUIRE_CASE(case_name, source->apu_noise.timer <= GBB_APU_NOISE_TIMER_MAX);
    source->apu_power = 0u;
    apu_power_off(source);
    REQUIRE_CASE(case_name, source->apu_noise.timer == 0u);
    uint32_t maximum_reload = 0u;
    /* NR43 retains all eight bits: divisor 112 and shift 15 are both reachable. */
    for (unsigned polynomial = 0u; polynomial <= UINT8_MAX; ++polynomial) {
        source->apu_noise.polynomial = (uint8_t)polynomial;
        const uint32_t reload = apu_noise_period(&source->apu_noise);
        if (reload > maximum_reload) maximum_reload = reload;
    }
    REQUIRE_CASE(case_name, maximum_reload == GBB_APU_NOISE_TIMER_MAX);
    source->apu_power = 1u;
    write8(source, 0xFF22u, 0xF7u);
    write8(source, 0xFF21u, 0xF0u);
    write8(source, 0xFF23u, 0x80u);
    REQUIRE_CASE(case_name, source->apu_noise.timer == GBB_APU_NOISE_TIMER_MAX &&
                            source->apu_noise.enabled == 1);

    size_t size = 0u;
    REQUIRE_CASE(case_name, gbb_state_size(source, &size) == GBB_OK);
    const state_field_descriptor *timer_field = state_field_by_path("apu_noise.timer");
    REQUIRE_CASE(case_name, timer_field != NULL &&
                            state_field_value_valid(source, timer_field, 0u,
                                GBB_APU_NOISE_TIMER_MAX,
                                source->audio_event_head, source->apu_sample_phase, NULL) &&
                            !state_field_value_valid(source, timer_field, 0u,
                                GBB_APU_NOISE_TIMER_MAX + 1u,
                                source->audio_event_head, source->apu_sample_phase, NULL));
    uint8_t *saved = malloc(size);
    uint8_t *resaved = malloc(size);
    uint8_t *above_bound = malloc(size);
    REQUIRE_CASE(case_name, saved != NULL && resaved != NULL && above_bound != NULL);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE(case_name, gbb_load_state(target, saved, size) == GBB_OK);
    REQUIRE_CASE(case_name, target->apu_noise.timer == GBB_APU_NOISE_TIMER_MAX);
    REQUIRE_CASE(case_name, gbb_save_state(target, resaved, size) == GBB_OK &&
                            memcmp(saved, resaved, size) == 0);

    gbb_audio_frame source_audio[1024], target_audio[1024];
    size_t source_count = 0u, target_count = 0u;
    const gbb_run_result source_run = gbb_run_audio(source, 140448u, source_audio,
                                                     1024u, &source_count);
    const gbb_run_result target_run = gbb_run_audio(target, 140448u, target_audio,
                                                     1024u, &target_count);
    REQUIRE_CASE(case_name, source_run.reason == GBB_STOP_BUDGET &&
                            same_run(source_run, target_run));
    REQUIRE_CASE(case_name, source_count == target_count &&
                            memcmp(source_audio, target_audio,
                                   source_count * sizeof(source_audio[0])) == 0);
    REQUIRE_CASE(case_name, source->apu_noise.timer < GBB_APU_NOISE_TIMER_MAX &&
                            target->apu_noise.timer == source->apu_noise.timer);
    const uint64_t remaining_before_expiry =
        GBB_APU_NOISE_TIMER_MAX - source_run.consumed_half_dots;
    const gbb_run_result source_tail = gbb_run(source, 7500000u, NULL, 0u);
    const gbb_run_result target_tail = gbb_run(target, 7500000u, NULL, 0u);
    REQUIRE_CASE(case_name, source_tail.reason == GBB_STOP_BUDGET &&
                            same_run(source_tail, target_tail) &&
                            source_tail.consumed_half_dots > remaining_before_expiry);
    REQUIRE_CASE(case_name, source->apu_noise.timer > 0u &&
                            source->apu_noise.timer <= GBB_APU_NOISE_TIMER_MAX &&
                            target->apu_noise.timer == source->apu_noise.timer);
    REQUIRE_CASE(case_name, gbb_save_state(source, saved, size) == GBB_OK &&
                            gbb_save_state(target, resaved, size) == GBB_OK &&
                            memcmp(saved, resaved, size) == 0);

    memcpy(above_bound, saved, size);
    REQUIRE_CASE(case_name, state_internal_write_field(target, above_bound,
                                                       "apu_noise.timer",
                                                       GBB_APU_NOISE_TIMER_MAX + 1u));
    state_internal_rechecksum(above_bound, size);
    state_instance_snapshot snapshot;
    REQUIRE_CASE(case_name, state_snapshot_init(&snapshot, target));
    target->apu_noise.timer = 1234u;
    state_snapshot_capture(&snapshot, target);
    REQUIRE_CASE(case_name, state_expect_refusal_unchanged(&snapshot, target,
        above_bound, size, GBB_STATE_INVALID_CONTENT));

    state_snapshot_destroy(&snapshot);
    free(above_bound);
    free(resaved);
    free(saved);
    gbb_destroy(target);
    gbb_destroy(source);
    puts("state_apu_noise_timer pass reload_max=7340032 countdown=expiry-reload roundtrip=continuation-equal above_bound=crc-valid-refused unchanged=1");
    return 0;
}

/* Unrelated smoke control for mutation builds: the state size/save path stays
 * usable when a load-only observer or RTC policy is mutated. */
static int state_control(void) {
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x10u, 0u);
    gbb_instance *machine = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    if (machine == NULL) return 1;
    size_t size = 0u;
    int ok = gbb_state_size(machine, &size) == GBB_OK;
    uint8_t *state = ok ? malloc(size + 1u) : NULL;
    ok = ok && state != NULL && gbb_save_state(machine, state, size) == GBB_OK;
    free(state);
    gbb_destroy(machine);
    if (!ok) return 1;
    puts("state_control pass size/save");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "state_rtc_palette") == 0) return state_rtc_palette();
    if (strcmp(argv[1], "state_observers") == 0) return state_observers();
    if (strcmp(argv[1], "state_refusal") == 0) return state_refusal();
    if (strcmp(argv[1], "state_refusal_controls") == 0) return state_refusal_controls();
    if (strcmp(argv[1], "state_apu_pulse_timer") == 0) return state_apu_pulse_timer();
    if (strcmp(argv[1], "state_apu_noise_timer") == 0) return state_apu_noise_timer();
    if (strcmp(argv[1], "state_control") == 0) return state_control();
    fprintf(stderr, "unknown state internal case: %s\n", argv[1]);
    return 2;
}
