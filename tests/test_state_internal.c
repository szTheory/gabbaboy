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
    uint8_t *saved = malloc(state_size);
    uint8_t *resaved = malloc(state_size);
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

/* Unrelated smoke control for mutation builds: the state size/save path stays
 * usable when a load-only observer or RTC policy is mutated. */
static int state_control(void) {
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, 0x10u, 0u);
    gbb_instance *machine = new_machine(rom, GBB_PROFILE_CGB_CPU_E);
    if (machine == NULL) return 1;
    size_t size = 0u;
    int ok = gbb_state_size(machine, &size) == GBB_OK;
    uint8_t *state = ok ? malloc(size) : NULL;
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
    if (strcmp(argv[1], "state_control") == 0) return state_control();
    fprintf(stderr, "unknown state internal case: %s\n", argv[1]);
    return 2;
}
