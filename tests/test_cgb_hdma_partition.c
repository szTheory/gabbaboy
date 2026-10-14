/* Private split-run checks share the established ownership-aware partition oracle. */
#define main cgb_partition_existing_main
#include "test_cgb_partition.c"
#undef main

#define HDMA_PARTITION_TOTAL UINT64_C(270000)
#define HDMA_OUTPUT_TOTAL UINT64_C(8192)
#define HDMA_TRACE_CAPACITY 8192u
#define HDMA_DIAGNOSTIC_CAPACITY 16384u

typedef struct {
    gbb_trace_record *trace;
    size_t trace_count;
    gbb_diagnostic_record *diagnostics;
    size_t diagnostic_count;
} hdma_trace_streams;

static void hdma_make_rom(uint8_t rom[32768], uint8_t control,
                          int cancel_before_speed_switch) {
    uint8_t program[80] = {
        0xF3u,                              /* DI while timer is prepared */
        0x3Eu, 0x04u, 0xEAu, 0xFFu, 0xFFu, /* IE = timer */
        0x3Eu, 0x00u, 0xE0u, 0x0Fu,       /* IF = 0 */
        0x3Eu, 0xFEu, 0xE0u, 0x05u,       /* TIMA = FE */
        0x3Eu, 0x00u, 0xE0u, 0x06u,       /* TMA = 0 */
        0x3Eu, 0x01u, 0xE0u, 0x4Fu,       /* VBK = 1 */
        0x3Eu, 0xC0u, 0xE0u, 0x51u,       /* HDMA1 = C0 */
        0x3Eu, 0x00u, 0xE0u, 0x52u,       /* HDMA2 = 00 */
        0x3Eu, 0x80u, 0xE0u, 0x53u,       /* HDMA3 = 80 */
        0x3Eu, 0x00u, 0xE0u, 0x54u        /* HDMA4 = 00 */
    };
    size_t program_size = 38u;
    const uint8_t enable_and_start[] = {
        0xFBu, 0x00u,                     /* EI; NOP */
        0x3Eu, 0x05u, 0xE0u, 0x07u,      /* start timer immediately before DMA */
        0x3Eu, 0x00u, 0xE0u, 0x55u       /* real CPU-programmed DMA request */
    };
    memcpy(program + program_size, enable_and_start, sizeof(enable_and_start));
    program_size += sizeof(enable_and_start);
    program[program_size - 3u] = control;
    if ((control & 0x80u) != 0u) {
        if (cancel_before_speed_switch) {
            const uint8_t cancel[] = {0x3Eu, 0x00u, 0xE0u, 0x55u};
            memcpy(program + program_size, cancel, sizeof(cancel));
            program_size += sizeof(cancel);
        }
        const uint8_t switch_speed[] = {
            0x3Eu, 0x01u, 0xE0u, 0x4Du,   /* arm KEY1 while HBlank DMA waits */
            0x10u, 0x00u                 /* STOP; HDMA may run during speed pause */
        };
        memcpy(program + program_size, switch_speed, sizeof(switch_speed));
        program_size += sizeof(switch_speed);
        if ((control & 0x7Fu) != 0u && !cancel_before_speed_switch) {
            const uint8_t cancel[] = {0x3Eu, 0x00u, 0xE0u, 0x55u};
            memcpy(program + program_size, cancel, sizeof(cancel));
            program_size += sizeof(cancel);
        }
    }
    program[program_size++] = 0x18u;
    program[program_size++] = 0xFEu;
    memset(rom, 0, 32768u);
    rom[0x143u] = 0xC0u;
    rom[0x147u] = 0x00u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x00u;
    memcpy(rom + 0x100u, program, program_size);
    static const uint8_t timer_handler[] = {
        0xF3u, 0x3Eu, 0x00u, 0xE0u, 0x07u, /* DI; stop further timer requests */
        0x3Eu, 0xA5u, 0xEAu, 0x00u, 0xC1u, /* observable natural IRQ marker */
        0xD9u                               /* RETI */
    };
    memcpy(rom + 0x50u, timer_handler, sizeof(timer_handler));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int hdma_machine_create_scenario(unsigned double_speed, uint8_t control,
                                        int cancel_before_speed_switch,
                                        partition_machine *out) {
    uint8_t rom[32768];
    hdma_make_rom(rom, control, cancel_before_speed_switch);
    memset(out, 0, sizeof(*out));
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &out->machine) != GBB_OK) return 1;
    if (gbb_load_rom(out->machine, rom, sizeof(rom)) != GBB_OK) {
        partition_machine_destroy(out);
        return 1;
    }
    out->machine->pc = 0x100u;
    out->machine->double_speed = (uint8_t)(double_speed != 0u);
    for (size_t i = 0u; i < 16u; ++i)
        out->machine->wram[0][i] = (uint8_t)(0x31u + i * 7u);
    const gbb_input_event input = {
        .at_half_dots = 900u,
        .kind = GBB_INPUT_BUTTON_PRESS,
        .value = GBB_BUTTON_A
    };
    if (gbb_queue_events(out->machine, &input, 1u) != GBB_OK) {
        partition_machine_destroy(out);
        return 1;
    }
    return 0;
}

static int hdma_machine_create_mode(unsigned double_speed, uint8_t control,
                                    partition_machine *out) {
    return hdma_machine_create_scenario(double_speed, control, 0, out);
}

static int hdma_machine_create(unsigned double_speed, partition_machine *out) {
    return hdma_machine_create_mode(double_speed, 0x00u, out);
}

static int hdma_guest_transfer_valid(const gbb_instance *machine) {
    if (machine->hdma.mode != 0u || machine->hdma.active != 0u ||
        machine->hdma.pending_hblank != 0u || machine->hdma.blocks_remaining != 0u ||
        machine->hdma.block_vram_bank != 1u) {
        fputs("hdma-partition-guest-transfer-incomplete\n", stderr);
        return 0;
    }
    if (machine->wram[0][0x100u] != 0xA5u) {
        fprintf(stderr, "hdma-partition-natural-timer-wake-missing pc=%04x ie=%02x if=%02x ime=%d tac=%02x tima=%02x timer-reload=%d/%u time=%" PRIu64 "\n",
                machine->pc, machine->ie, machine->interrupt_flags, machine->ime,
                machine->tac, machine->tima, machine->timer_reload_pending,
                machine->timer_reload_remaining, machine->time_half_dots);
        return 0;
    }
    for (size_t i = 0u; i < 16u; ++i) {
        if (machine->vram[1][i] != machine->wram[0][i]) {
            fprintf(stderr, "hdma-partition-guest-byte-mismatch index=%zu\n", i);
            return 0;
        }
    }
    return 1;
}

static int hdma_audio_call(partition_machine *run, uint64_t budget,
                           partition_meter *meter) {
    gbb_audio_frame frames[8192];
    size_t frame_count = 0u;
    gbb_run_result result = gbb_run_audio(run->machine, budget, frames,
        sizeof(frames) / sizeof(frames[0]), &frame_count);
    if (result.reason != GBB_STOP_BUDGET ||
        partition_meter_add(meter, result.consumed_half_dots) != 0 ||
        partition_append_audio(&run->streams, frames, frame_count) != 0)
        return -1;
    if (!run->machine->serial_active) run->streams.serial_tracking = 0u;
    return (int)result.consumed_half_dots;
}

static int hdma_trace_create(hdma_trace_streams *out) {
    memset(out, 0, sizeof(*out));
    out->trace = calloc(HDMA_TRACE_CAPACITY, sizeof(*out->trace));
    out->diagnostics = calloc(HDMA_DIAGNOSTIC_CAPACITY, sizeof(*out->diagnostics));
    if (out->trace == NULL || out->diagnostics == NULL) {
        free(out->trace);
        free(out->diagnostics);
        memset(out, 0, sizeof(*out));
        return -1;
    }
    return 0;
}

static void hdma_trace_destroy(hdma_trace_streams *streams) {
    free(streams->trace);
    free(streams->diagnostics);
    memset(streams, 0, sizeof(*streams));
}

static int hdma_trace_call(partition_machine *run, hdma_trace_streams *streams,
                           uint64_t budget) {
    gbb_trace_record trace[2048];
    gbb_diagnostic_record diagnostics[8192];
    gbb_run_result result = gbb_run_ex(run->machine, budget, trace,
        sizeof(trace) / sizeof(trace[0]), diagnostics,
        sizeof(diagnostics) / sizeof(diagnostics[0]));
    if (result.reason != GBB_STOP_BUDGET ||
        result.trace_count > HDMA_TRACE_CAPACITY - streams->trace_count ||
        result.diagnostic_count > HDMA_DIAGNOSTIC_CAPACITY - streams->diagnostic_count)
        return -1;
    memcpy(streams->trace + streams->trace_count, trace,
           result.trace_count * sizeof(*trace));
    streams->trace_count += result.trace_count;
    memcpy(streams->diagnostics + streams->diagnostic_count, diagnostics,
           result.diagnostic_count * sizeof(*diagnostics));
    streams->diagnostic_count += result.diagnostic_count;
    return (int)result.consumed_half_dots;
}

static int hdma_run_audio(partition_machine *run, const uint64_t *cuts,
                          size_t cut_count, uint64_t total, int drop_remainders,
                          uint64_t *consumed_out) {
    partition_meter meter = {0};
    uint64_t previous = 0u;
    uint64_t pending = 0u;
    for (size_t i = 0u; i < cut_count; ++i) {
        if (cuts[i] < previous || cuts[i] > total) return 1;
        pending += cuts[i] - previous;
        previous = cuts[i];
        if (pending != 0u) {
            int consumed = hdma_audio_call(run, pending, &meter);
            if (consumed < 0) return 1;
            pending -= (uint64_t)consumed;
            if (drop_remainders) pending = 0u;
        }
    }
    pending += total - previous;
    if (pending != 0u) {
        int consumed = hdma_audio_call(run, pending, &meter);
        if (consumed < 0) return 1;
        pending -= (uint64_t)consumed;
    }
    *consumed_out = meter.consumed_half_dots;
    return 0;
}

static int hdma_run_trace(partition_machine *run, hdma_trace_streams *streams,
                          const uint64_t *cuts, size_t cut_count,
                          uint64_t total, uint64_t *consumed_out) {
    uint64_t previous = 0u;
    uint64_t pending = 0u;
    uint64_t consumed_total = 0u;
    for (size_t i = 0u; i < cut_count; ++i) {
        if (cuts[i] < previous || cuts[i] > total) return 1;
        pending += cuts[i] - previous;
        previous = cuts[i];
        if (pending != 0u) {
            int consumed = hdma_trace_call(run, streams, pending);
            if (consumed < 0) return 1;
            pending -= (uint64_t)consumed;
            consumed_total += (uint64_t)consumed;
        }
    }
    pending += total - previous;
    if (pending != 0u) {
        int consumed = hdma_trace_call(run, streams, pending);
        if (consumed < 0) return 1;
        pending -= (uint64_t)consumed;
        consumed_total += (uint64_t)consumed;
    }
    *consumed_out = consumed_total;
    return 0;
}

static int hdma_trace_equal(const hdma_trace_streams *a,
                            const hdma_trace_streams *b) {
    if (a->trace_count != b->trace_count ||
        a->diagnostic_count != b->diagnostic_count) return 0;
    for (size_t i = 0u; i < a->trace_count; ++i) {
        const gbb_trace_record *x = &a->trace[i];
        const gbb_trace_record *y = &b->trace[i];
        if (x->time_half_dots != y->time_half_dots || x->pc != y->pc ||
            x->opcode_size != y->opcode_size || memcmp(x->opcode, y->opcode, 3u) != 0 ||
            x->a != y->a || x->f != y->f || x->b != y->b || x->c != y->c ||
            x->d != y->d || x->e != y->e || x->h != y->h || x->l != y->l ||
            x->sp != y->sp) return 0;
    }
    for (size_t i = 0u; i < a->diagnostic_count; ++i) {
        const gbb_diagnostic_record *x = &a->diagnostics[i];
        const gbb_diagnostic_record *y = &b->diagnostics[i];
        if (x->time_half_dots != y->time_half_dots || x->kind != y->kind ||
            x->pc != y->pc || x->opcode != y->opcode || x->address != y->address ||
            x->value != y->value || x->timer_state != y->timer_state) return 0;
    }
    return 1;
}

static int hdma_compare_audio(unsigned speed, const uint64_t *cuts,
                              size_t cut_count, int drop_remainders,
                              uint64_t *reference_consumed_out) {
    partition_machine reference, split;
    REQUIRE(hdma_machine_create(speed, &reference) == 0);
    REQUIRE(hdma_machine_create(speed, &split) == 0);
    uint64_t reference_consumed = 0u, split_consumed = 0u;
    REQUIRE(hdma_run_audio(&reference, NULL, 0u, HDMA_PARTITION_TOTAL, 0,
                           &reference_consumed) == 0);
    const int guest_valid = hdma_guest_transfer_valid(reference.machine);
    REQUIRE(hdma_run_audio(&split, cuts, cut_count, HDMA_PARTITION_TOTAL,
                           drop_remainders, &split_consumed) == 0);
    const uint64_t expected = partition_digest(reference.machine, &reference.streams);
    const uint64_t actual = partition_digest(split.machine, &split.streams);
    const int equal = guest_valid && expected == actual &&
        reference_consumed == split_consumed;
    if (reference_consumed_out != NULL) *reference_consumed_out = reference_consumed;
    if (!equal)
        fprintf(stderr, "hdma-partition-mismatch speed=%u consumed=%" PRIu64 "/%" PRIu64
                        " expected=%016" PRIx64 " actual=%016" PRIx64 "\n",
                speed, reference_consumed, split_consumed, expected, actual);
    partition_machine_destroy(&reference);
    partition_machine_destroy(&split);
    return equal ? 0 : 1;
}

static int hdma_compare_trace(unsigned speed, const uint64_t *cuts,
                              size_t cut_count) {
    partition_machine reference, split;
    hdma_trace_streams reference_streams, split_streams;
    REQUIRE(hdma_machine_create(speed, &reference) == 0);
    REQUIRE(hdma_machine_create(speed, &split) == 0);
    REQUIRE(hdma_trace_create(&reference_streams) == 0);
    REQUIRE(hdma_trace_create(&split_streams) == 0);
    uint64_t reference_consumed = 0u, split_consumed = 0u;
    const int run_failed =
        hdma_run_trace(&reference, &reference_streams, NULL, 0u,
                       HDMA_OUTPUT_TOTAL, &reference_consumed) != 0 ||
        hdma_run_trace(&split, &split_streams, cuts, cut_count,
                       HDMA_OUTPUT_TOTAL, &split_consumed) != 0;
    const int equal = !run_failed && reference_consumed == split_consumed &&
        partition_digest(reference.machine, &reference.streams) ==
            partition_digest(split.machine, &split.streams) &&
        hdma_trace_equal(&reference_streams, &split_streams);
    if (!equal) fprintf(stderr, "hdma-partition-output-mismatch speed=%u\n", speed);
    partition_machine_destroy(&reference);
    partition_machine_destroy(&split);
    hdma_trace_destroy(&reference_streams);
    hdma_trace_destroy(&split_streams);
    return equal ? 0 : 1;
}

static int hdma_find_cut_scenario(unsigned speed, uint8_t control,
                                  int cancel_before_speed_switch, int event,
                                  uint64_t *out_cut) {
    partition_machine run;
    REQUIRE(hdma_machine_create_scenario(speed, control,
        cancel_before_speed_switch, &run) == 0);
    partition_meter meter = {0};
    uint64_t pending = 0u;
    int transfer_started = 0;
    int saw_speed_stall = 0;
    for (uint64_t requested = 1u; requested <= HDMA_PARTITION_TOTAL;) {
        uint64_t step = 1u;
        if (event != 7 && saw_speed_stall &&
            run.machine->cpu_stall_half_dots > 128u)
            step = 64u;
        if (step > HDMA_PARTITION_TOTAL - requested + 1u)
            step = HDMA_PARTITION_TOTAL - requested + 1u;
        pending += step;
        int consumed = hdma_audio_call(&run, pending, &meter);
        if (consumed < 0) {
            partition_machine_destroy(&run);
            return 1;
        }
        pending -= (uint64_t)consumed;
        const hdma_state *hdma = &run.machine->hdma;
        if (hdma->active || hdma->pending_hblank || hdma->blocks_remaining != 0u)
            transfer_started = 1;
        if (run.machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
            run.machine->cpu_stall_half_dots != 0u)
            saw_speed_stall = 1;
        const int match = event == 0
            ? hdma->active && hdma->byte_index == 0u
            : event == 1
                ? hdma->active && hdma->byte_index >= 1u
                : event == 2
                    ? transfer_started && hdma->mode == 0u && hdma->active == 0u &&
                        hdma->pending_hblank == 0u && hdma->blocks_remaining == 0u
                    : event == 3
                        ? saw_speed_stall && run.machine->cpu_stall_half_dots == 0u &&
                            run.machine->double_speed != speed
                        : event == 4
                            ? hdma->mode == 1u && hdma->active == 0u
                            : event == 5
                                ? transfer_started && hdma->mode == 0u &&
                                    hdma->active == 0u && hdma->pending_hblank == 0u &&
                                    hdma->control_readback == 0x80u
                                : event == 6
                                    ? run.machine->wram[0][0x100u] == 0xA5u
                                    : event == 7
                                        ? hdma->mode == 1u && hdma->active != 0u &&
                                            hdma->byte_index == 15u
                                        : event == 8 && hdma->mode == 1u &&
                                            hdma->active == 0u && hdma->byte_index == 0u &&
                                            hdma->blocks_remaining == 15u;
        if (match) {
            *out_cut = requested;
            partition_machine_destroy(&run);
            return 0;
        }
        requested += step;
    }
    fprintf(stderr, "hdma-partition-last-state pc=%04x t=%" PRIu64 " mode=%u active=%u pending=%u remaining=%u phase=%u stall=%u/%u speed=%u marker=%02x\n",
            run.machine->pc, run.machine->time_half_dots, run.machine->hdma.mode,
            run.machine->hdma.active, run.machine->hdma.pending_hblank,
            run.machine->hdma.blocks_remaining, run.machine->hdma.byte_phase,
            run.machine->cpu_stall_kind, run.machine->cpu_stall_half_dots,
            run.machine->double_speed, run.machine->wram[0][0x100u]);
    partition_machine_destroy(&run);
    fprintf(stderr, "hdma-partition-event-not-found speed=%u control=%02x event=%d\n",
            speed, control, event);
    return 1;
}

static int hdma_find_cut(unsigned speed, uint8_t control, int event,
                         uint64_t *out_cut) {
    return hdma_find_cut_scenario(speed, control, 0, event, out_cut);
}

static int hdma_compare_cancel(unsigned speed, const uint64_t *cuts,
                               size_t cut_count) {
    partition_machine reference, split;
    REQUIRE(hdma_machine_create_scenario(speed, 0x8Fu, 1, &reference) == 0);
    REQUIRE(hdma_machine_create_scenario(speed, 0x8Fu, 1, &split) == 0);
    uint64_t reference_consumed = 0u, split_consumed = 0u;
    REQUIRE(hdma_run_audio(&reference, NULL, 0u, HDMA_PARTITION_TOTAL, 0,
        &reference_consumed) == 0);
    REQUIRE(hdma_run_audio(&split, cuts, cut_count, HDMA_PARTITION_TOTAL, 0,
        &split_consumed) == 0);
    const int cancelled = reference.machine->hdma.mode == 0u &&
        reference.machine->hdma.active == 0u &&
        reference.machine->hdma.pending_hblank == 0u &&
        reference.machine->hdma.blocks_remaining == 0u &&
        reference.machine->hdma.control_readback == 0x80u;
    const int equal = cancelled && reference_consumed == split_consumed &&
        partition_digest(reference.machine, &reference.streams) ==
            partition_digest(split.machine, &split.streams);
    if (!equal) fputs("hdma-partition-cancel-window-mismatch\n", stderr);
    partition_machine_destroy(&reference);
    partition_machine_destroy(&split);
    return equal ? 0 : 1;
}

static int cgb_hdma_partition_midbyte(void) {
    partition_machine prefix, restored, reference;
    partition_snap snapshot;
    uint64_t cut = 0u;
    REQUIRE(hdma_find_cut(1u, 0x00u, 0, &cut) == 0);
    REQUIRE(hdma_machine_create(1u, &prefix) == 0);
    REQUIRE(hdma_machine_create(1u, &restored) == 0);
    REQUIRE(hdma_machine_create(1u, &reference) == 0);
    partition_meter prefix_meter = {0}, reference_meter = {0};
    REQUIRE(hdma_audio_call(&prefix, cut, &prefix_meter) >= 0);
    REQUIRE(prefix.machine->hdma.active != 0u &&
            prefix.machine->hdma.byte_phase != 0u);
    REQUIRE(partition_snapshot(&prefix, &snapshot) == 0);
    REQUIRE(partition_restore(&restored, &snapshot) == 0);

    const uint64_t digest = partition_digest(prefix.machine, &prefix.streams);
    static const char *const fields[] = {
        "mode", "active", "pending_hblank", "blocks_remaining", "byte_index",
        "byte_phase", "source_cursor", "destination_cursor", "block_vram_bank",
        "source_high", "source_low", "destination_high", "destination_low",
        "control_readback", "cpu_stall_half_dots"
    };
    for (size_t i = 0u; i < sizeof(fields) / sizeof(fields[0]); ++i) {
        gbb_instance changed = *prefix.machine;
        switch (i) {
            case 0u: changed.hdma.mode ^= 1u; break;
            case 1u: changed.hdma.active ^= 1u; break;
            case 2u: changed.hdma.pending_hblank ^= 1u; break;
            case 3u: changed.hdma.blocks_remaining ^= 1u; break;
            case 4u: changed.hdma.byte_index ^= 1u; break;
            case 5u: changed.hdma.byte_phase ^= 1u; break;
            case 6u: changed.hdma.source_cursor ^= 1u; break;
            case 7u: changed.hdma.destination_cursor ^= 1u; break;
            case 8u: changed.hdma.block_vram_bank ^= 1u; break;
            case 9u: changed.hdma.source_high ^= 1u; break;
            case 10u: changed.hdma.source_low ^= 1u; break;
            case 11u: changed.hdma.destination_high ^= 1u; break;
            case 12u: changed.hdma.destination_low ^= 1u; break;
            case 13u: changed.hdma.control_readback ^= 1u; break;
            case 14u: changed.cpu_stall_half_dots ^= 1u; break;
            default: return 1;
        }
        if (partition_digest(&changed, &prefix.streams) == digest) {
            fprintf(stderr, "hdma-partition-digest-omitted-field %s\n", fields[i]);
            partition_snapshot_destroy(&snapshot);
            partition_machine_destroy(&prefix);
            partition_machine_destroy(&restored);
            partition_machine_destroy(&reference);
            return 1;
        }
    }

    uint64_t expected_consumed = 0u, split_consumed = prefix_meter.consumed_half_dots;
    REQUIRE(hdma_run_audio(&reference, NULL, 0u, HDMA_PARTITION_TOTAL, 0,
                           &expected_consumed) == 0);
    partition_meter suffix_meter = {0};
    const uint64_t remaining_budget = HDMA_PARTITION_TOTAL - cut +
        (cut - prefix_meter.consumed_half_dots);
    REQUIRE(hdma_audio_call(&restored, remaining_budget, &suffix_meter) >= 0);
    split_consumed += suffix_meter.consumed_half_dots;
    const uint64_t expected = partition_digest(reference.machine, &reference.streams);
    const uint64_t actual = partition_digest(restored.machine, &restored.streams);
    if (!hdma_guest_transfer_valid(reference.machine) ||
        !hdma_guest_transfer_valid(restored.machine) ||
        expected != actual || expected_consumed != split_consumed) {
        fprintf(stderr, "hdma-partition-midbyte-mismatch cut=%" PRIu64 "\n", cut);
        partition_snapshot_destroy(&snapshot);
        partition_machine_destroy(&prefix);
        partition_machine_destroy(&restored);
        partition_machine_destroy(&reference);
        return 1;
    }
    partition_snapshot_destroy(&snapshot);
    partition_machine_destroy(&prefix);
    partition_machine_destroy(&restored);
    partition_machine_destroy(&reference);
    printf("cgb_hdma_partition_midbyte pass cut=%" PRIu64 " consumed=%" PRIu64 "\n",
           cut, split_consumed);
    return 0;
}

static int cgb_hdma_partition_windows(void) {
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        for (size_t mode = 0u; mode < 2u; ++mode) {
            const uint8_t control = mode == 0u ? 0x00u : 0x8Fu;
            uint64_t before = 0u, after = 0u, complete = 0u, pause_end = 0u;
            uint64_t pending_edge = 0u, last_byte = 0u, first_block_end = 0u;
            uint64_t irq_wake = 0u;
            REQUIRE(hdma_find_cut(speed, control, 0, &before) == 0);
            REQUIRE(hdma_find_cut(speed, control, 1, &after) == 0);
            REQUIRE(hdma_find_cut(speed, control, 2, &complete) == 0);
            if (mode != 0u) {
                REQUIRE(hdma_find_cut(speed, control, 4, &pending_edge) == 0);
                REQUIRE(hdma_find_cut(speed, control, 7, &last_byte) == 0);
                REQUIRE(hdma_find_cut(speed, control, 8, &first_block_end) == 0);
                REQUIRE(hdma_find_cut(speed, control, 3, &pause_end) == 0);
            } else {
                REQUIRE(hdma_find_cut(speed, control, 6, &irq_wake) == 0);
            }
            uint64_t cuts[24] = {
                before > 8u ? before - 8u : 0u, before, before + 1u,
                after > 1u ? after - 1u : after, after, after + 1u,
                complete > 8u ? complete - 8u : 0u, complete, complete + 1u,
                pause_end > 8u ? pause_end - 8u : 0u, pause_end,
                pause_end != 0u ? pause_end + 1u : 0u
            };
            size_t cut_count = 12u;
            if (mode == 0u) {
                cuts[cut_count++] = irq_wake > 8u ? irq_wake - 8u : 0u;
                cuts[cut_count++] = irq_wake;
                cuts[cut_count++] = irq_wake + 1u;
            } else {
                cuts[cut_count++] = pending_edge > 1u ? pending_edge - 1u : 0u;
                cuts[cut_count++] = pending_edge;
                cuts[cut_count++] = pending_edge + 1u;
                cuts[cut_count++] = last_byte > 1u ? last_byte - 1u : 0u;
                cuts[cut_count++] = last_byte;
                cuts[cut_count++] = last_byte + 1u;
                cuts[cut_count++] = first_block_end > 1u ? first_block_end - 1u : 0u;
                cuts[cut_count++] = first_block_end;
                cuts[cut_count++] = first_block_end + 1u;
            }
            for (size_t i = 1u; i < cut_count; ++i) {
                uint64_t item = cuts[i];
                size_t j = i;
                while (j != 0u && cuts[j - 1u] > item) {
                    cuts[j] = cuts[j - 1u];
                    --j;
                }
                cuts[j] = item;
            }
            if (mode == 0u) {
                REQUIRE(hdma_compare_audio(speed, cuts,
                    cut_count, 0, NULL) == 0);
            } else {
                partition_machine reference, split;
                REQUIRE(hdma_machine_create_mode(speed, control, &reference) == 0);
                REQUIRE(hdma_machine_create_mode(speed, control, &split) == 0);
                uint64_t consumed_reference = 0u, consumed_split = 0u;
                REQUIRE(hdma_run_audio(&reference, NULL, 0u, HDMA_PARTITION_TOTAL, 0,
                    &consumed_reference) == 0);
                REQUIRE(hdma_run_audio(&split, cuts, cut_count,
                    HDMA_PARTITION_TOTAL, 0, &consumed_split) == 0);
                REQUIRE(hdma_guest_transfer_valid(reference.machine));
                REQUIRE(consumed_reference == consumed_split);
                REQUIRE(partition_digest(reference.machine, &reference.streams) ==
                        partition_digest(split.machine, &split.streams));
                partition_machine_destroy(&reference);
                partition_machine_destroy(&split);
            }
        }
        uint64_t cancel_pending = 0u, cancelled = 0u, cancel_pause_end = 0u;
        REQUIRE(hdma_find_cut_scenario(speed, 0x8Fu, 1, 4, &cancel_pending) == 0);
        REQUIRE(hdma_find_cut_scenario(speed, 0x8Fu, 1, 5, &cancelled) == 0);
        REQUIRE(hdma_find_cut_scenario(speed, 0x8Fu, 1, 3, &cancel_pause_end) == 0);
        uint64_t cancel_cuts[] = {
            cancel_pending > 1u ? cancel_pending - 1u : 0u,
            cancel_pending, cancel_pending + 1u,
            cancelled > 1u ? cancelled - 1u : 0u,
            cancelled, cancelled + 1u,
            cancel_pause_end > 8u ? cancel_pause_end - 8u : 0u,
            cancel_pause_end, cancel_pause_end + 1u
        };
        for (size_t i = 1u; i < sizeof(cancel_cuts) / sizeof(cancel_cuts[0]); ++i) {
            uint64_t item = cancel_cuts[i];
            size_t j = i;
            while (j != 0u && cancel_cuts[j - 1u] > item) {
                cancel_cuts[j] = cancel_cuts[j - 1u];
                --j;
            }
            cancel_cuts[j] = item;
        }
        REQUIRE(hdma_compare_cancel(speed, cancel_cuts,
            sizeof(cancel_cuts) / sizeof(cancel_cuts[0])) == 0);
    }
    puts("cgb_hdma_partition_windows pass speeds=2 block-admission+last-byte+cancel+irq+pause-end");
    return 0;
}

static int cgb_hdma_partition_multicut(void) {
    static const uint32_t seeds[] = {0x13A04u, 0x77D15u, 0xC6B22u};
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        for (size_t seed_index = 0u; seed_index < sizeof(seeds) / sizeof(seeds[0]); ++seed_index) {
            uint32_t random = seeds[seed_index];
            uint64_t cuts[32];
            for (size_t i = 0u; i < sizeof(cuts) / sizeof(cuts[0]); ++i) {
                random = random * 1664525u + 1013904223u;
                cuts[i] = 1u + random % (uint32_t)(HDMA_PARTITION_TOTAL - 1u);
            }
            for (size_t i = 1u; i < sizeof(cuts) / sizeof(cuts[0]); ++i) {
                uint64_t item = cuts[i];
                size_t j = i;
                while (j != 0u && cuts[j - 1u] > item) {
                    cuts[j] = cuts[j - 1u];
                    --j;
                }
                cuts[j] = item;
            }
            REQUIRE(hdma_compare_audio(speed, cuts,
                sizeof(cuts) / sizeof(cuts[0]), 0, NULL) == 0);
        }
    }
    puts("cgb_hdma_partition_multicut pass seeds=3 speeds=2 cuts=32");
    return 0;
}

static int cgb_hdma_partition_outputs(void) {
    const uint64_t cuts[] = {101u, 399u, 400u, 401u, 777u, 1213u, 2049u, 3071u};
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        REQUIRE(hdma_compare_audio(speed, cuts,
            sizeof(cuts) / sizeof(cuts[0]), 0, NULL) == 0);
        REQUIRE(hdma_compare_trace(speed, cuts,
            sizeof(cuts) / sizeof(cuts[0])) == 0);
    }
    puts("cgb_hdma_partition_outputs pass audio=frames trace=timestamped diagnostics=timestamped");
    return 0;
}

static int cgb_hdma_partition_lost_remainder_control(void) {
    const uint64_t cuts[] = {403u, 404u, 405u, 811u, 1207u};
    uint64_t reference_consumed = 0u;
    if (hdma_compare_audio(1u, cuts, sizeof(cuts) / sizeof(cuts[0]), 1,
                          &reference_consumed) == 0) {
        fputs("hdma-partition-control-lost-remainder-inert\n", stderr);
        return 1;
    }
    printf("hdma-partition-control-detected lost-remainder reference=%" PRIu64 "\n",
           reference_consumed);
    return 1;
}

static int cgb_hdma_partition_order_control(void) {
    partition_machine run;
    hdma_trace_streams streams, reversed;
    REQUIRE(hdma_machine_create(1u, &run) == 0);
    REQUIRE(hdma_trace_create(&streams) == 0);
    REQUIRE(hdma_trace_create(&reversed) == 0);
    uint64_t consumed = 0u;
    REQUIRE(hdma_run_trace(&run, &streams, NULL, 0u,
        HDMA_OUTPUT_TOTAL, &consumed) == 0);
    if (streams.trace_count < 2u) {
        fputs("hdma-partition-control-insufficient-trace\n", stderr);
        partition_machine_destroy(&run);
        hdma_trace_destroy(&streams);
        hdma_trace_destroy(&reversed);
        return 1;
    }
    memcpy(reversed.trace, streams.trace,
           streams.trace_count * sizeof(*streams.trace));
    memcpy(reversed.diagnostics, streams.diagnostics,
           streams.diagnostic_count * sizeof(*streams.diagnostics));
    reversed.trace_count = streams.trace_count;
    reversed.diagnostic_count = streams.diagnostic_count;
    gbb_trace_record swap = reversed.trace[0];
    reversed.trace[0] = reversed.trace[1];
    reversed.trace[1] = swap;
    const int rejected = !hdma_trace_equal(&streams, &reversed);
    partition_machine_destroy(&run);
    hdma_trace_destroy(&streams);
    hdma_trace_destroy(&reversed);
    if (!rejected) {
        fputs("hdma-partition-control-order-inert\n", stderr);
        return 1;
    }
    fputs("hdma-partition-control-detected event-order\n", stderr);
    return 1;
}

static void mutant_phase_rom(uint8_t rom[32768]) {
    memset(rom, 0, 32768u);
    rom[0x143u] = 0xC0u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int mutant_phase_machine(gbb_instance **out) {
    uint8_t rom[32768];
    mutant_phase_rom(rom);
    *out = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, out) != GBB_OK ||
        gbb_load_rom(*out, rom, sizeof(rom)) != GBB_OK) {
        if (*out != NULL) gbb_destroy(*out);
        *out = NULL;
        fputs("hdma mutant lost_phase fixture setup failed\n", stderr);
        return 1;
    }
    gbb_instance *m = *out;
    for (unsigned i = 0u; i < 16u; ++i)
        m->wram[0][i] = (uint8_t)(0x31u + 11u * i);
    memset(m->vram[0], 0xA5, sizeof(m->vram[0]));
    m->hdma.mode = 2u;
    m->hdma.active = 1u;
    m->hdma.blocks_remaining = 1u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->hdma.block_vram_bank = 0u;
    return 0;
}

static int cgb_hdma_partition_mutant_lost_phase(void) {
    gbb_instance *whole = NULL, *split = NULL;
    REQUIRE(mutant_phase_machine(&whole) == 0);
    REQUIRE(mutant_phase_machine(&split) == 0);
    gbb_run_result one = gbb_run(whole, 4u, NULL, 0u);
    REQUIRE(one.consumed_half_dots == 4u);
    for (unsigned cut = 0u; cut < 4u; ++cut) {
        gbb_run_result part = gbb_run(split, 1u, NULL, 0u);
        REQUIRE(part.consumed_half_dots == 1u);
    }
    const int equal = whole->time_half_dots == split->time_half_dots &&
        whole->hdma.active == split->hdma.active &&
        whole->hdma.byte_phase == split->hdma.byte_phase &&
        whole->hdma.blocks_remaining == split->hdma.blocks_remaining &&
        memcmp(whole->vram[0], split->vram[0], sizeof(whole->vram[0])) == 0;
    gbb_destroy(whole);
    gbb_destroy(split);
    if (!equal) {
        fputs("hdma mutant lost_phase detected one-call versus four-cut state predicate\n", stderr);
        return 1;
    }
    puts("cgb-hdma mutant_lost_phase pass");
    return 0;
}

int main(int argc, char **argv) {
#ifdef GBB_P12_MUTANT_BUILD
    if (argc >= 4 && strcmp(argv[argc - 2], "--mutants") == 0) {
        char *end = NULL;
        unsigned long long mask = strtoull(argv[argc - 1], &end, 0);
        if (end == argv[argc - 1] || *end != '\0') return 2;
        gbb_p12_set_mutants((uint64_t)mask);
        argc -= 2;
    }
#endif
    if (argc != 2) return 2;
    if (strcmp(argv[1], "midbyte") == 0) return cgb_hdma_partition_midbyte();
    if (strcmp(argv[1], "windows") == 0) return cgb_hdma_partition_windows();
    if (strcmp(argv[1], "multicut") == 0) return cgb_hdma_partition_multicut();
    if (strcmp(argv[1], "outputs") == 0) return cgb_hdma_partition_outputs();
    if (strcmp(argv[1], "lost_remainder_control") == 0)
        return cgb_hdma_partition_lost_remainder_control();
    if (strcmp(argv[1], "order_control") == 0)
        return cgb_hdma_partition_order_control();
    if (strcmp(argv[1], "mutant_lost_phase") == 0)
        return cgb_hdma_partition_mutant_lost_phase();
    return 2;
}
