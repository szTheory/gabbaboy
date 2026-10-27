/* White-box fork tests over the public save/load calls. The included core is
 * used only to poison a receiving instance and record the actual serialized
 * field values at a public save boundary. */
#ifndef GBB_CORE_SOURCE_PATH
#define GBB_CORE_SOURCE_PATH "../src/core/gabbaboy.c"
#endif
#include GBB_CORE_SOURCE_PATH

#include <stdio.h>
#include <stdlib.h>

#define FRAME_PIXELS (GBB_FRAME_WIDTH * GBB_FRAME_HEIGHT)
#define FORK_AUDIO_CAPACITY 2048u

static void set_palette(gbb_compat_palette *palette, uint16_t seed) {
    memset(palette, 0, sizeof(*palette));
    palette->struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    for (size_t i = 0u; i < 4u; ++i) {
        palette->bg[i] = (uint16_t)((seed + i * 0x31u) & 0x7FFFu);
        palette->obj0[i] = (uint16_t)((seed + 0x100u + i * 0x53u) & 0x7FFFu);
        palette->obj1[i] = (uint16_t)((seed + 0x200u + i * 0x71u) & 0x7FFFu);
    }
}

static int read_file(const char *path, uint8_t **out_bytes, size_t *out_size) {
    *out_bytes = NULL;
    *out_size = 0u;
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
                           gbb_profile profile) {
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
    const uint64_t prefix_budget = UINT64_C(140448);
    gbb_audio_frame prefix_audio[FORK_AUDIO_CAPACITY];
    size_t prefix_count = 0u;
    const gbb_run_result prefix = gbb_run_audio(source, prefix_budget,
        prefix_audio, FORK_AUDIO_CAPACITY, &prefix_count);
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
    queued.at_half_dots = source->time_half_dots + UINT64_C(70000);
    queued.kind = GBB_INPUT_BUTTON_PRESS;
    queued.value = GBB_BUTTON_A;
    if (gbb_queue_events(source, &queued, 1u) != GBB_OK) {
        fprintf(stderr, "state-fork setup failure: queued input: %s\n", case_id);
        gbb_destroy(target);
        gbb_destroy(baseline);
        gbb_destroy(source);
        return 2;
    }

    size_t state_size = 0u;
    if (gbb_state_size(source, &state_size) != GBB_OK) {
        fprintf(stderr, "state-fork setup failure: state size: %s\n", case_id);
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
        equal = equal && projection_equal;
        free(target_battery); free(source_battery);
    }

    const int final_saved = gbb_save_state(source, source_final, state_size) == GBB_OK &&
        gbb_save_state(target, target_final, state_size) == GBB_OK &&
        memcmp(source_final, target_final, state_size) == 0;
    if (!final_saved) fprintf(stderr, "state-fork mismatch: final canonical bytes case=%s\n", case_id);
    equal = equal && final_saved;
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
    if (argc == 5 && strcmp(argv[1], "case") == 0) {
        const gbb_profile profile = strcmp(argv[4], "cgb") == 0
            ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B;
        return state_fork_case(argv[2], argv[3], profile);
    }
    fprintf(stderr, "usage: test_state_fork state_slice_invariance | case ID ROM dmg|cgb\n");
    return 2;
}
