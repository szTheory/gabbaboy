/* White-box operational-horizon tests. The test uses valid ROM identity and
 * the production codec to create boundary states; it does not forge CRCs
 * except for the explicit ordinary-time cap+1 refusal case. */
#ifndef GBB_CORE_SOURCE_PATH
#define GBB_CORE_SOURCE_PATH "../src/core/gabbaboy.c"
#endif
#include GBB_CORE_SOURCE_PATH

#include <stdio.h>
#include <stdlib.h>

#define TEST_ROM_BYTES 0x8000u
#define TEST_HORIZON (UINT64_C(1) << 62)

static const char *failed_reason;

static int fail_case(const char *reason) {
    failed_reason = reason;
    return 0;
}

#define REQUIRE_CASE(condition, reason) do { \
    if (!(condition)) return fail_case(reason); \
} while (0)

static void fix_header_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0u; i < 0x19u; ++i)
        checksum = (uint8_t)(checksum - rom[0x134u + i] - 1u);
    rom[0x14Du] = checksum;
}

static void build_rom(uint8_t rom[TEST_ROM_BYTES], uint8_t cgb_flag) {
    memset(rom, 0, TEST_ROM_BYTES);
    rom[0x143u] = cgb_flag;
    rom[0x147u] = 0u;
    rom[0x148u] = 0u;
    rom[0x149u] = 0u;
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    rom[0x200u] = 0x00u; /* NOP, eight master half-dots at normal speed. */
    rom[0x210u] = 0x10u; /* STOP, 00. */
    rom[0x211u] = 0x00u;
    rom[0x220u] = 0xE2u; /* LDH (C), A; tests the whole-block HDMA reservation. */
    fix_header_checksum(rom);
}

static gbb_instance *new_machine(gbb_profile profile) {
    uint8_t rom[TEST_ROM_BYTES];
    build_rom(rom, profile == GBB_PROFILE_CGB_CPU_E ? 0x80u : 0u);
    gbb_instance *machine = NULL;
    if (gbb_create(profile, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static void seed_time(gbb_instance *machine, uint64_t now) {
    machine->time_half_dots = now;
    machine->instruction_start_half_dots = now;
    if (machine->cart.has_timer) machine->cart.rtc_synced_at = now;
}

static int save_snapshot(const gbb_instance *machine, uint8_t **bytes, size_t *size) {
    *bytes = NULL;
    *size = 0u;
    if (gbb_state_size(machine, size) != GBB_OK) return 0;
    *bytes = (uint8_t *)malloc(*size);
    if (*bytes == NULL) return 0;
    if (gbb_save_state(machine, *bytes, *size) != GBB_OK) {
        free(*bytes);
        *bytes = NULL;
        return 0;
    }
    return 1;
}

static size_t state_body_offset(const gbb_instance *machine, const char *path) {
    size_t offset = 0u;
    const size_t count = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    for (size_t i = 0u; i < count; ++i) {
        const state_field_descriptor *field = &STATE_FIELDS[i];
        if (strcmp(field->path, path) == 0) return offset;
        offset += state_field_count_for_instance(machine, field) * field->wire_width;
    }
    return SIZE_MAX;
}

static void rechecksum_state(uint8_t *bytes) {
    const size_t body_size = (size_t)state_get_u32(bytes + 52u);
    uint32_t crc = state_crc32_update(UINT32_MAX, bytes, 60u);
    crc = state_crc32_update(crc, bytes + GBB_STATE_HEADER_BYTES, body_size) ^ UINT32_MAX;
    state_put_u32(bytes + 60u, crc);
}

static int branch_no_progress(const char *reason, gbb_instance *machine,
                              uint64_t budget) {
    const gbb_instance before = *machine;
    const gbb_run_result result = gbb_run(machine, budget, NULL, 0u);
    if (result.reason != GBB_STOP_NO_PROGRESS || result.consumed_half_dots != 0u) {
        fprintf(stderr, "expected no progress; actual reason=%d consumed=%llu now=%llu\n",
                (int)result.reason, (unsigned long long)result.consumed_half_dots,
                (unsigned long long)machine->time_half_dots);
        return fail_case(reason);
    }
    REQUIRE_CASE(memcmp(&before, machine, sizeof(before)) == 0, reason);
    return 1;
}

static int horizon_stop_wait(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: valid DMG machine creation");
    seed_time(machine, TEST_HORIZON - 2u);
    machine->stopped = 1u;
    const gbb_run_result result = gbb_run(machine, 4u, NULL, 0u);
    REQUIRE_CASE(result.reason == GBB_STOP_NO_PROGRESS &&
                 result.consumed_half_dots == 2u &&
                 machine->time_half_dots == TEST_HORIZON && machine->stopped,
                 "horizon discrepancy: stop-wait");
    gbb_destroy(machine);
    return 1;
}

static int horizon_cpu_stall(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(machine != NULL, "fixture: valid CGB machine creation");
    seed_time(machine, TEST_HORIZON);
    machine->cpu_stall_kind = GBB_STALL_SWITCH_REALIGN;
    machine->cpu_stall_half_dots = 4u;
    const int result = branch_no_progress("horizon discrepancy: cpu-stall", machine, 4u);
    gbb_destroy(machine);
    return result;
}

static int horizon_hdma_tick(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(machine != NULL, "fixture: valid CGB machine creation");
    seed_time(machine, TEST_HORIZON);
    machine->hdma.mode = 2u;
    machine->hdma.active = 1u;
    machine->hdma.blocks_remaining = 1u;
    machine->hdma.source_cursor = 0x0200u;
    machine->hdma.destination_cursor = 0x8000u;
    machine->hdma.block_vram_bank = 0u;
    const int result = branch_no_progress("horizon discrepancy: hdma-tick", machine, 1u);
    gbb_destroy(machine);
    return result;
}

static int horizon_irq(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: valid DMG machine creation");
    seed_time(machine, TEST_HORIZON);
    machine->ime = 1u;
    machine->ie = 1u;
    machine->interrupt_flags = 1u;
    const int result = branch_no_progress("horizon discrepancy: irq", machine, 40u);
    gbb_destroy(machine);
    return result;
}

static int horizon_halt(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: valid DMG machine creation");
    seed_time(machine, TEST_HORIZON);
    machine->halted = 1u;
    const int result = branch_no_progress("horizon discrepancy: halt", machine, 8u);
    gbb_destroy(machine);
    return result;
}

static int horizon_instruction(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: valid DMG machine creation");
    seed_time(machine, TEST_HORIZON - 1u);
    machine->pc = 0x0200u;
    const int result = branch_no_progress("horizon discrepancy: instruction", machine, 8u);
    gbb_destroy(machine);
    return result;
}

static int horizon_speed_switch(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(machine != NULL && machine->exec_mode == GBB_MODE_CGB,
                 "fixture: CGB speed-switch mode");
    machine->pc = 0x0210u;
    machine->key1_armed = 1u;
    const uint64_t reserve = (uint64_t)GBB_STOP_SWITCH_COST_HALF_DOTS +
        2u * (uint64_t)GBB_SPEED_SWITCH_STALL_T + 4u;
    seed_time(machine, TEST_HORIZON - reserve + 1u);
    const int result = branch_no_progress(
        "horizon discrepancy: speed-switch-reservation", machine,
        GBB_STOP_SWITCH_COST_HALF_DOTS);
    gbb_destroy(machine);
    return result;
}

static int horizon_hdma_reservation(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(machine != NULL && machine->exec_mode == GBB_MODE_CGB,
                 "fixture: CGB HDMA-reservation mode");
    machine->pc = 0x0220u;
    machine->a = 0x80u;
    machine->c = 0x55u;
    seed_time(machine, TEST_HORIZON - 16u);
    const int result = branch_no_progress(
        "horizon discrepancy: hdma-reservation", machine, 16u);
    gbb_destroy(machine);
    return result;
}

static int horizon_peripheral(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(machine != NULL, "fixture: valid CGB machine creation");
    seed_time(machine, TEST_HORIZON - 1u);
    const gbb_instance before = *machine;
    advance_devices(machine, 2u);
    REQUIRE_CASE(memcmp(&before, machine, sizeof(before)) == 0,
                 "horizon discrepancy: peripheral-addition");
    gbb_destroy(machine);
    return 1;
}

static int horizon_exact_fit(void) {
    gbb_instance *source = new_machine(GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(source != NULL && target != NULL, "fixture: exact-fit machines");
    source->pc = 0x0200u;
    seed_time(source, TEST_HORIZON - 8u);
    source->dma_active = 1u;
    source->dma_page = 0xC0u;
    source->dma_index = 0u;
    source->dma_phase = (uint8_t)(GBB_T_PER_M - 1u);
    uint8_t *before = NULL;
    size_t before_size = 0u;
    REQUIRE_CASE(save_snapshot(source, &before, &before_size),
                 "fixture: save genuine cap-minus-cost state");
    const gbb_run_result result = gbb_run(source, 8u, NULL, 0u);
    REQUIRE_CASE(result.reason == GBB_STOP_BUDGET &&
                 result.consumed_half_dots == 8u &&
                 source->time_half_dots == TEST_HORIZON && source->dma_index > 0u,
                 "horizon discrepancy: exact-fit peripheral advancement");
    uint8_t *after = NULL;
    size_t after_size = 0u;
    REQUIRE_CASE(save_snapshot(source, &after, &after_size) && after_size == before_size,
                 "closure discrepancy: exact-fit state is not saveable");
    REQUIRE_CASE(gbb_load_state(target, after, after_size) == GBB_OK,
                 "closure discrepancy: exact-fit state is not loadable");
    uint8_t *roundtrip = NULL;
    size_t roundtrip_size = 0u;
    REQUIRE_CASE(save_snapshot(target, &roundtrip, &roundtrip_size) &&
                 roundtrip_size == after_size &&
                 memcmp(after, roundtrip, after_size) == 0,
                 "closure discrepancy: exact-fit resave changed bytes");
    free(roundtrip);
    free(after);
    free(before);
    gbb_destroy(target);
    gbb_destroy(source);
    return 1;
}

static int horizon_wrappers(void) {
    for (unsigned wrapper = 0u; wrapper < 5u; ++wrapper) {
        gbb_instance *machine = new_machine(GBB_PROFILE_CGB_CPU_E);
        REQUIRE_CASE(machine != NULL, "fixture: wrapper machine creation");
        machine->pc = 0x0200u;
        seed_time(machine, TEST_HORIZON);
        uint8_t *before = NULL;
        size_t before_size = 0u;
        REQUIRE_CASE(save_snapshot(machine, &before, &before_size),
                     "fixture: wrapper boundary state is saveable");
        gbb_run_result result = {0};
        if (wrapper == 0u) {
            puts("# horizon witness: wrapper gbb_run");
            result = gbb_run(machine, 8u, NULL, 0u);
        } else if (wrapper == 1u) {
            puts("# horizon witness: wrapper gbb_run_ex");
            gbb_trace_record trace[1] = {{0}};
            gbb_diagnostic_record diagnostics[1] = {{0}};
            result = gbb_run_ex(machine, 8u, trace, 1u, diagnostics, 1u);
        } else if (wrapper == 2u) {
            puts("# horizon witness: wrapper gbb_run_audio");
            gbb_audio_frame frames[1] = {{0}};
            size_t count = SIZE_MAX;
            result = gbb_run_audio(machine, 8u, frames, 1u, &count);
            REQUIRE_CASE(count == 0u, "horizon discrepancy: wrapper audio output count");
        } else {
            size_t cursor = 0u;
            const gbb_accept_input_span span = {NULL, 0u, &cursor};
            if (wrapper == 3u) {
                puts("# horizon witness: wrapper gbb_accept_run_diagnostic");
                result = gbb_accept_run_diagnostic(machine, 8u, &span, NULL, 0u,
                                                   NULL, 0u);
            } else {
                puts("# horizon witness: wrapper gbb_accept_run_audio");
                gbb_audio_frame frames[1] = {{0}};
                size_t count = SIZE_MAX;
                result = gbb_accept_run_audio(machine, 8u, &span, frames, 1u, &count);
                REQUIRE_CASE(count == 0u && cursor == 0u,
                             "horizon discrepancy: wrapper accepted audio outputs");
            }
        }
        if (result.reason != GBB_STOP_NO_PROGRESS || result.consumed_half_dots != 0u ||
            machine->time_half_dots != TEST_HORIZON) {
            fprintf(stderr, "wrapper=%u actual reason=%d consumed=%llu now=%llu\n",
                    wrapper, (int)result.reason,
                    (unsigned long long)result.consumed_half_dots,
                    (unsigned long long)machine->time_half_dots);
            return fail_case("horizon discrepancy: public or acceptance wrapper");
        }
        uint8_t *after = NULL;
        size_t after_size = 0u;
        REQUIRE_CASE(save_snapshot(machine, &after, &after_size) &&
                     after_size == before_size &&
                     memcmp(before, after, before_size) == 0,
                     "closure discrepancy: wrapper changed a blocked state");
        free(after);
        free(before);
        gbb_destroy(machine);
    }
    return 1;
}

static int horizon_sentinels(void) {
    gbb_instance *source = new_machine(GBB_PROFILE_CGB_CPU_E);
    gbb_instance *target = new_machine(GBB_PROFILE_CGB_CPU_E);
    REQUIRE_CASE(source != NULL && target != NULL, "fixture: sentinel machines");
    seed_time(source, TEST_HORIZON);
    source->timer_reloaded_at = UINT64_MAX;
    uint8_t *state = NULL;
    size_t state_size = 0u;
    REQUIRE_CASE(save_snapshot(source, &state, &state_size),
                 "fixture: cap state with timer sentinel is valid");
    REQUIRE_CASE(gbb_load_state(target, state, state_size) == GBB_OK &&
                 target->timer_reloaded_at == UINT64_MAX,
                 "horizon discrepancy: valid UINT64_MAX timer sentinel rejected");
    target->pc = 0x0200u;
    const int blocked = branch_no_progress("horizon discrepancy: sentinel continuation",
                                           target, 8u);
    REQUIRE_CASE(blocked, "horizon discrepancy: sentinel continuation");
    uint8_t *over_cap = (uint8_t *)malloc(state_size);
    REQUIRE_CASE(over_cap != NULL, "fixture: allocate hostile state copy");
    memcpy(over_cap, state, state_size);
    const size_t offset = state_body_offset(source, "time_half_dots");
    REQUIRE_CASE(offset != SIZE_MAX, "fixture: locate serialized ordinary time");
    state_put_u64(over_cap + GBB_STATE_HEADER_BYTES + offset, TEST_HORIZON + 1u, 8u);
    rechecksum_state(over_cap);
    REQUIRE_CASE(gbb_load_state(target, over_cap, state_size) == GBB_STATE_INVALID_CONTENT,
                 "horizon discrepancy: ordinary cap+1 state accepted");

    target->time_half_dots = TEST_HORIZON + 1u;
    target->instruction_start_half_dots = TEST_HORIZON + 1u;
    const gbb_instance invalid_state = *target;
    const gbb_run_result invalid = gbb_run(target, 8u, NULL, 0u);
    REQUIRE_CASE(invalid.reason == GBB_STOP_INVALID_STATE &&
                 invalid.consumed_half_dots == 0u &&
                 memcmp(&invalid_state, target, sizeof(invalid_state)) == 0,
                 "horizon discrepancy: over-cap live state was not refused unchanged");
    free(over_cap);
    free(state);
    gbb_destroy(target);
    gbb_destroy(source);
    return 1;
}

static int horizon_event_admission(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    gbb_instance *target = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL && target != NULL, "fixture: event admission machines");
    seed_time(machine, TEST_HORIZON - 2u);
    const gbb_input_event boundary[] = {
        {TEST_HORIZON - 1u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {TEST_HORIZON, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    REQUIRE_CASE(gbb_queue_events(machine, boundary, 2u) == GBB_OK,
                 "horizon discrepancy: cap-minus-one and cap events rejected");
    REQUIRE_CASE(machine->input_event_count == 2u &&
                 memcmp(machine->input_events, boundary, sizeof(boundary)) == 0,
                 "horizon discrepancy: event order changed on admission");
    const gbb_instance before_cap_plus_one = *machine;
    const gbb_input_event cap_plus_one = {
        TEST_HORIZON + 1u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_B
    };
    const gbb_error over_cap = gbb_queue_events(machine, &cap_plus_one, 1u);
    if (over_cap != GBB_INVALID_EVENT) {
        fprintf(stderr, "ordinary event cap+1 actual error=%d count=%zu\n",
                (int)over_cap, machine->input_event_count);
        return fail_case("horizon discrepancy: ordinary-event cap+1 admitted");
    }
    REQUIRE_CASE(memcmp(&before_cap_plus_one, machine, sizeof(before_cap_plus_one)) == 0,
                 "horizon discrepancy: rejected event changed the queue");
    const gbb_input_event before_current = {
        TEST_HORIZON - 3u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_B
    };
    REQUIRE_CASE(gbb_queue_events(machine, &before_current, 1u) == GBB_INVALID_EVENT &&
                 memcmp(&before_cap_plus_one, machine, sizeof(before_cap_plus_one)) == 0,
                 "horizon discrepancy: before-current event was not transactional");
    uint8_t *state = NULL;
    size_t state_size = 0u;
    REQUIRE_CASE(save_snapshot(machine, &state, &state_size),
                 "closure discrepancy: accepted cap event queue cannot be saved");
    REQUIRE_CASE(gbb_load_state(target, state, state_size) == GBB_OK &&
                 target->input_event_count == 2u &&
                 memcmp(target->input_events, boundary, sizeof(boundary)) == 0,
                 "closure discrepancy: loaded event order changed");
    free(state);
    gbb_destroy(target);
    gbb_destroy(machine);

    machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: full event queue machine");
    seed_time(machine, TEST_HORIZON);
    gbb_input_event full[GBB_INPUT_EVENT_CAPACITY];
    for (size_t i = 0u; i < GBB_INPUT_EVENT_CAPACITY; ++i)
        full[i] = (gbb_input_event){TEST_HORIZON, GBB_INPUT_BUTTON_PRESS,
                                   (uint8_t)(i % 8u)};
    REQUIRE_CASE(gbb_queue_events(machine, full, GBB_INPUT_EVENT_CAPACITY) == GBB_OK,
                 "horizon discrepancy: full queue at cap rejected");
    const gbb_instance full_before = *machine;
    REQUIRE_CASE(gbb_queue_events(machine, full, 1u) == GBB_EVENT_QUEUE_FULL &&
                 memcmp(&full_before, machine, sizeof(full_before)) == 0,
                 "horizon discrepancy: full queue admission changed state");
    const gbb_instance empty_before = *machine;
    REQUIRE_CASE(gbb_queue_events(machine, NULL, 0u) == GBB_OK &&
                 memcmp(&empty_before, machine, sizeof(empty_before)) == 0,
                 "horizon discrepancy: empty event batch changed state");
    gbb_destroy(machine);
    return 1;
}

static int horizon_span_admission(void) {
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: borrowed span machine");
    seed_time(machine, TEST_HORIZON - 2u);
    size_t cursor = 0u;
    const gbb_input_event over_cap_event = {
        TEST_HORIZON + 1u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A
    };
    const gbb_accept_input_span over_cap = {&over_cap_event, 1u, &cursor};
    const gbb_instance before = *machine;
    const gbb_run_result rejected = gbb_accept_run_diagnostic(
        machine, 8u, &over_cap, NULL, 0u, NULL, 0u);
    REQUIRE_CASE(rejected.reason == GBB_STOP_INVALID_STATE &&
                 rejected.consumed_half_dots == 0u && cursor == 0u &&
                 memcmp(&before, machine, sizeof(before)) == 0,
                 "horizon discrepancy: borrowed span cap+1 admitted or mutated");

    gbb_audio_frame frames[1] = {{0}};
    size_t frame_count = SIZE_MAX;
    const gbb_run_result rejected_audio = gbb_accept_run_audio(
        machine, 8u, &over_cap, frames, 1u, &frame_count);
    REQUIRE_CASE(rejected_audio.reason == GBB_STOP_INVALID_STATE &&
                 rejected_audio.consumed_half_dots == 0u && frame_count == 0u &&
                 cursor == 0u && memcmp(&before, machine, sizeof(before)) == 0,
                 "horizon discrepancy: audio span cap+1 admitted or mutated");

    const gbb_input_event past_event = {
        TEST_HORIZON - 3u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A
    };
    const gbb_accept_input_span stale = {&past_event, 1u, &cursor};
    const gbb_run_result stale_result = gbb_accept_run_diagnostic(
        machine, 8u, &stale, NULL, 0u, NULL, 0u);
    REQUIRE_CASE(stale_result.reason == GBB_STOP_INVALID_STATE && cursor == 0u &&
                 memcmp(&before, machine, sizeof(before)) == 0,
                 "horizon discrepancy: span suffix before current time admitted");

    const gbb_input_event reversed_events[] = {
        {TEST_HORIZON, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {TEST_HORIZON - 1u, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    const gbb_accept_input_span reversed = {reversed_events, 2u, &cursor};
    const gbb_run_result reversed_result = gbb_accept_run_diagnostic(
        machine, 8u, &reversed, NULL, 0u, NULL, 0u);
    REQUIRE_CASE(reversed_result.reason == GBB_STOP_INVALID_STATE && cursor == 0u &&
                 memcmp(&before, machine, sizeof(before)) == 0,
                 "horizon discrepancy: reversed span admitted");

    const gbb_accept_input_span too_many = {NULL, SIZE_MAX, &cursor};
    const gbb_run_result count_overflow = gbb_accept_run_diagnostic(
        machine, 8u, &too_many, NULL, 0u, NULL, 0u);
    REQUIRE_CASE(count_overflow.reason == GBB_STOP_INVALID_STATE && cursor == 0u &&
                 memcmp(&before, machine, sizeof(before)) == 0,
                 "horizon discrepancy: overflowing span extent admitted");
    gbb_destroy(machine);

    machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: same-time span machine");
    machine->pc = 0x0200u;
    seed_time(machine, TEST_HORIZON - 8u);
    machine->serial_active = 1u;
    machine->serial_control = 0x80u;
    machine->serial_edge_remaining = 0u;
    machine->serial_data = 0u;
    machine->serial_bits = 0u;
    const gbb_input_event same_time[] = {
        {TEST_HORIZON - 9u, GBB_INPUT_SERIAL_EDGE, 0u},
        {TEST_HORIZON, GBB_INPUT_SERIAL_EDGE, 1u},
        {TEST_HORIZON, GBB_INPUT_SERIAL_EDGE, 0u}
    };
    cursor = 1u; /* The historical prefix remains in caller-owned span order. */
    const gbb_accept_input_span ordered = {same_time, 3u, &cursor};
    const gbb_run_result accepted = gbb_accept_run_diagnostic(
        machine, 8u, &ordered, NULL, 0u, NULL, 0u);
    REQUIRE_CASE(accepted.reason == GBB_STOP_BUDGET &&
                 accepted.consumed_half_dots == 8u &&
                 machine->time_half_dots == TEST_HORIZON && cursor == 3u &&
                 machine->serial_data == 2u && machine->serial_bits == 2u,
                 "horizon discrepancy: same-time span order or CPU collision changed");
    uint8_t *after = NULL;
    size_t after_size = 0u;
    REQUIRE_CASE(save_snapshot(machine, &after, &after_size),
                 "closure discrepancy: same-time span result cannot be saved");
    REQUIRE_CASE(gbb_load_state(machine, after, after_size) == GBB_OK,
                 "closure discrepancy: same-time span result cannot be reloaded");
    uint8_t *roundtrip = NULL;
    size_t roundtrip_size = 0u;
    REQUIRE_CASE(save_snapshot(machine, &roundtrip, &roundtrip_size) &&
                 roundtrip_size == after_size &&
                 memcmp(after, roundtrip, after_size) == 0,
                 "closure discrepancy: same-time span resave changed bytes");
    free(roundtrip);
    free(after);
    gbb_destroy(machine);
    return 1;
}

static int horizon_events(void) {
    return horizon_event_admission() && horizon_span_admission();
}

static int compare_u64(const void *left, const void *right) {
    const uint64_t a = *(const uint64_t *)left;
    const uint64_t b = *(const uint64_t *)right;
    return a < b ? -1 : a > b ? 1 : 0;
}

static int add_phase(uint64_t *phases, size_t *count, size_t capacity, uint64_t value) {
    if (phases == NULL || count == NULL || *count >= capacity) return 0;
    phases[(*count)++] = value;
    return 1;
}

static int horizon_closure(size_t shard, size_t shard_count) {
    if (shard_count == 0u || shard >= shard_count)
        return fail_case("fixture: invalid closure shard");
    gbb_instance *machine = new_machine(GBB_PROFILE_DMG_CPU_B);
    REQUIRE_CASE(machine != NULL, "fixture: closure machine");
    size_t state_size = 0u;
    REQUIRE_CASE(gbb_state_size(machine, &state_size) == GBB_OK,
                 "fixture: closure state size");
    uint8_t *baseline = NULL;
    uint8_t *before = (uint8_t *)malloc(state_size);
    uint8_t *after = (uint8_t *)malloc(state_size);
    uint8_t *roundtrip = (uint8_t *)malloc(state_size);
    uint8_t *blocked = (uint8_t *)malloc(state_size);
    REQUIRE_CASE(before != NULL && after != NULL && roundtrip != NULL && blocked != NULL &&
                 save_snapshot(machine, &baseline, &state_size),
                 "fixture: allocate closure state buffers");

    uint64_t phases[4096];
    size_t phase_count = 0u;
    REQUIRE_CASE(add_phase(phases, &phase_count,
                           sizeof(phases) / sizeof(phases[0]), 0u) &&
                 add_phase(phases, &phase_count,
                           sizeof(phases) / sizeof(phases[0]),
                           GBB_AUDIO_CLOCK_HALF_DOTS - 1u),
                 "fixture: audio phase matrix capacity");
    for (uint64_t completed = 0u; completed < GBB_AUDIO_EVENT_TAPS; ++completed) {
        const uint64_t base = completed * GBB_AUDIO_CLOCK_HALF_DOTS;
        const uint64_t first_quotient = base / GBB_AUDIO_SAMPLE_RATE + 1u;
        const uint64_t last_quotient =
            (base + GBB_AUDIO_CLOCK_HALF_DOTS - 1u) / GBB_AUDIO_SAMPLE_RATE;
        for (uint64_t quotient = first_quotient; quotient <= last_quotient; ++quotient) {
            const uint64_t phase = quotient * GBB_AUDIO_SAMPLE_RATE - base;
            if (phase < GBB_AUDIO_CLOCK_HALF_DOTS)
                REQUIRE_CASE(add_phase(phases, &phase_count,
                                       sizeof(phases) / sizeof(phases[0]), phase),
                             "fixture: audio phase matrix capacity");
        }
    }
    /* Every phase at which one of the next eight bounded ticks can consume an
     * audio sample, plus the adjacent values, is a separate transition class. */
    for (uint64_t samples = 1u; samples <= 8u; ++samples) {
        const uint64_t boundary = GBB_AUDIO_CLOCK_HALF_DOTS -
                                  samples * GBB_AUDIO_SAMPLE_RATE;
        if (boundary > 0u)
            REQUIRE_CASE(add_phase(phases, &phase_count,
                                   sizeof(phases) / sizeof(phases[0]), boundary - 1u),
                         "fixture: audio phase matrix capacity");
        REQUIRE_CASE(add_phase(phases, &phase_count,
                               sizeof(phases) / sizeof(phases[0]), boundary),
                     "fixture: audio phase matrix capacity");
        if (boundary + 1u < GBB_AUDIO_CLOCK_HALF_DOTS)
            REQUIRE_CASE(add_phase(phases, &phase_count,
                                   sizeof(phases) / sizeof(phases[0]), boundary + 1u),
                         "fixture: audio phase matrix capacity");
    }
    qsort(phases, phase_count, sizeof(phases[0]), compare_u64);
    size_t unique_phases = 0u;
    for (size_t i = 0u; i < phase_count; ++i)
        if (unique_phases == 0u || phases[i] != phases[unique_phases - 1u])
            phases[unique_phases++] = phases[i];

    const gbb_input_event_kind kinds[] = {
        GBB_INPUT_BUTTON_PRESS, GBB_INPUT_BUTTON_RELEASE
    };
    gbb_input_event queue[GBB_INPUT_EVENT_CAPACITY];
    for (size_t i = 0u; i < GBB_INPUT_EVENT_CAPACITY; ++i)
        queue[i] = (gbb_input_event){TEST_HORIZON, kinds[i & 1u], (uint8_t)(i % 8u)};
    const uint8_t heads[] = {0u, GBB_AUDIO_EVENT_TAPS - 1u};
    size_t case_index = 0u;
    size_t case_count = 0u;
    for (size_t h = 0u; h < sizeof(heads) / sizeof(heads[0]); ++h) {
        const uint8_t head = heads[h];
        for (size_t p = 0u; p < unique_phases; ++p) {
            if (case_index++ % shard_count != shard) continue;
            ++case_count;
            const uint64_t phase = phases[p];
            REQUIRE_CASE(phase < GBB_AUDIO_CLOCK_HALF_DOTS,
                         "fixture: generated audio phase outside accepted domain");
            REQUIRE_CASE(gbb_load_state(machine, baseline, state_size) == GBB_OK,
                         "closure discrepancy: baseline reload failed");
            seed_time(machine, TEST_HORIZON - 8u);
            machine->pc = 0x0200u;
            machine->audio_event_head = head;
            machine->apu_sample_phase = phase;
            for (size_t offset = 0u; offset < GBB_AUDIO_EVENT_TAPS; ++offset) {
                const size_t slot = (offset + head) % GBB_AUDIO_EVENT_TAPS;
                const uint64_t completed = GBB_AUDIO_EVENT_TAPS - 1u - offset;
                const uint64_t past =
                    (completed * GBB_AUDIO_CLOCK_HALF_DOTS + phase) /
                    GBB_AUDIO_SAMPLE_RATE;
                REQUIRE_CASE(past <= UINT64_MAX /
                             GBB_STATE_AUDIO_MAX_EDGE_CONTRIBUTION,
                             "fixture: ring boundary multiplication overflow");
                const int64_t limit = (int64_t)(past *
                    GBB_STATE_AUDIO_MAX_EDGE_CONTRIBUTION);
                machine->audio_event_ring[0][slot] = limit;
                machine->audio_event_ring[1][slot] = -limit;
                REQUIRE_CASE(state_audio_ring_slot_valid(head, slot, phase, limit) &&
                             state_audio_ring_slot_valid(head, slot, phase, -limit),
                             "fixture: generated ring boundary rejected by validator");
            }
            REQUIRE_CASE(gbb_queue_events(machine, queue, GBB_INPUT_EVENT_CAPACITY) == GBB_OK,
                         "closure discrepancy: full equal-time queue rejected");
            REQUIRE_CASE(gbb_save_state(machine, before, state_size) == GBB_OK,
                         "closure discrepancy: hostile accepted boundary state cannot save");
            const gbb_run_result progress = gbb_run(machine, 8u, NULL, 0u);
            REQUIRE_CASE(progress.reason == GBB_STOP_BUDGET &&
                         progress.consumed_half_dots == 8u &&
                         machine->time_half_dots == TEST_HORIZON &&
                         machine->input_event_count == 0u,
                         "closure discrepancy: bounded operation did not reach exact cap");
            REQUIRE_CASE(gbb_save_state(machine, after, state_size) == GBB_OK &&
                         gbb_load_state(machine, after, state_size) == GBB_OK &&
                         gbb_save_state(machine, roundtrip, state_size) == GBB_OK &&
                         memcmp(after, roundtrip, state_size) == 0,
                         "closure discrepancy: exact-cap save/load/resave changed bytes");
            const gbb_run_result stopped = gbb_run(machine, 8u, NULL, 0u);
            REQUIRE_CASE(stopped.reason == GBB_STOP_NO_PROGRESS &&
                         stopped.consumed_half_dots == 0u &&
                         gbb_save_state(machine, blocked, state_size) == GBB_OK &&
                         memcmp(after, blocked, state_size) == 0,
                         "closure discrepancy: cap state escaped on the next bounded step");
        }
    }
    const size_t total_cases = unique_phases * (sizeof(heads) / sizeof(heads[0]));
    const size_t expected_cases = total_cases / shard_count +
        (shard < total_cases % shard_count ? 1u : 0u);
    REQUIRE_CASE(case_count == expected_cases,
                 "fixture: closure shard omitted or duplicated phase/head cases");
    printf("# closure witness: shard=%zu/%zu cases=%zu phase_classes=%zu heads=%zu\n",
           shard, shard_count, case_count, unique_phases,
           sizeof(heads) / sizeof(heads[0]));
    free(blocked);
    free(roundtrip);
    free(after);
    free(before);
    free(baseline);
    gbb_destroy(machine);
    return 1;
}

static int horizon_matrix(void) {
    return horizon_stop_wait() && horizon_cpu_stall() && horizon_hdma_tick() &&
           horizon_irq() && horizon_halt() && horizon_instruction() &&
           horizon_speed_switch() && horizon_hdma_reservation() &&
           horizon_peripheral() && horizon_exact_fit();
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    failed_reason = "unclassified horizon failure";
    printf("TAP version 13\n1..1\n");
    int passed = 0;
    if (strcmp(argv[1], "horizon_matrix") == 0) passed = horizon_matrix();
    else if (strcmp(argv[1], "horizon_stop_wait") == 0) passed = horizon_stop_wait();
    else if (strcmp(argv[1], "horizon_cpu_stall") == 0) passed = horizon_cpu_stall();
    else if (strcmp(argv[1], "horizon_hdma_tick") == 0) passed = horizon_hdma_tick();
    else if (strcmp(argv[1], "horizon_irq") == 0) passed = horizon_irq();
    else if (strcmp(argv[1], "horizon_halt") == 0) passed = horizon_halt();
    else if (strcmp(argv[1], "horizon_instruction") == 0) passed = horizon_instruction();
    else if (strcmp(argv[1], "horizon_speed_switch") == 0) passed = horizon_speed_switch();
    else if (strcmp(argv[1], "horizon_hdma_reservation") == 0) passed = horizon_hdma_reservation();
    else if (strcmp(argv[1], "horizon_peripheral") == 0) passed = horizon_peripheral();
    else if (strcmp(argv[1], "horizon_exact_fit") == 0) passed = horizon_exact_fit();
    else if (strcmp(argv[1], "horizon_wrappers") == 0) passed = horizon_wrappers();
    else if (strcmp(argv[1], "horizon_sentinels") == 0) passed = horizon_sentinels();
    else if (strcmp(argv[1], "horizon_events") == 0) passed = horizon_events();
    else if (strcmp(argv[1], "horizon_event_admission") == 0) passed = horizon_event_admission();
    else if (strcmp(argv[1], "horizon_span_admission") == 0) passed = horizon_span_admission();
    else if (strcmp(argv[1], "horizon_closure") == 0) {
        if (argc == 2) passed = horizon_closure(0u, 1u);
        else if (argc == 4) {
            char *end_shard = NULL;
            char *end_count = NULL;
            const unsigned long shard = strtoul(argv[2], &end_shard, 10);
            const unsigned long count = strtoul(argv[3], &end_count, 10);
            if (end_shard == argv[2] || *end_shard != '\0' ||
                end_count == argv[3] || *end_count != '\0' ||
                shard > SIZE_MAX || count > SIZE_MAX) return 2;
            passed = horizon_closure((size_t)shard, (size_t)count);
        } else return 2;
    }
    else return 2;
    if (passed) printf("ok 1 - %s\n", argv[1]);
    else printf("not ok 1 - %s\n  ---\n  message: %s\n  ...\n", argv[1], failed_reason);
    return passed ? 0 : 1;
}
