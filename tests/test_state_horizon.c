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

static int horizon_matrix(void) {
    return horizon_stop_wait() && horizon_cpu_stall() && horizon_hdma_tick() &&
           horizon_irq() && horizon_halt() && horizon_instruction() &&
           horizon_speed_switch() && horizon_hdma_reservation() &&
           horizon_peripheral() && horizon_exact_fit();
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
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
    else return 2;
    if (passed) printf("ok 1 - %s\n", argv[1]);
    else printf("not ok 1 - %s\n  ---\n  message: %s\n  ...\n", argv[1], failed_reason);
    return passed ? 0 : 1;
}
