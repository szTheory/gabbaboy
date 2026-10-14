/* White-box CGB speed-switch run partition checks (Phase 12 plan 12-14). */
#ifdef GBB_P12_CORE_SOURCE
#include GBB_P12_CORE_SOURCE
#else
#include "../src/core/gabbaboy.c"
#endif

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef GBB_P12_MUTANT_BUILD
extern uint64_t gbb_p12_mutants;
#endif

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define PARTITION_PREFIX_NOPS 15u
#define PARTITION_PCM_CAPACITY 8192u
#define PARTITION_SERIAL_CAPACITY 16u
#define PARTITION_FNV_OFFSET UINT64_C(0xCBF29CE484222325)
#define PARTITION_FNV_PRIME UINT64_C(0x100000001B3)
#ifndef GBB_PARTITION_CASE_HALF_DOT_CAP
#define GBB_PARTITION_CASE_HALF_DOT_CAP UINT64_C(6000000)
#endif

typedef struct {
    gbb_audio_frame pcm[PARTITION_PCM_CAPACITY];
    size_t pcm_count;
    uint8_t serial_output[PARTITION_SERIAL_CAPACITY];
    size_t serial_count;
    uint8_t serial_tracking;
} partition_streams;

typedef struct {
    unsigned start_double;
    unsigned pending_case;
    unsigned ime_on_at_stop;
    unsigned held_button;
    unsigned lcd_off;
    unsigned prepare_at_stall;
    unsigned timer_irq_in_stall;
    uint32_t seeded_stall_half_dots;
    uint64_t button_at_half_dots;
} partition_scenario;

typedef struct {
    uint64_t consumed_half_dots;
} partition_meter;

typedef struct {
    gbb_instance *machine;
    partition_streams streams;
} partition_machine;

static void hash_byte(uint64_t *hash, uint8_t value) {
    *hash ^= value;
    *hash *= PARTITION_FNV_PRIME;
}

static void hash_u16(uint64_t *hash, uint16_t value) {
    hash_byte(hash, (uint8_t)value);
    hash_byte(hash, (uint8_t)(value >> 8));
}

static void hash_u32(uint64_t *hash, uint32_t value) {
    for (unsigned i = 0u; i < 4u; ++i) hash_byte(hash, (uint8_t)(value >> (i * 8u)));
}

static void hash_u64(uint64_t *hash, uint64_t value) {
    for (unsigned i = 0u; i < 8u; ++i) hash_byte(hash, (uint8_t)(value >> (i * 8u)));
}

static void hash_bytes(uint64_t *hash, const void *data, size_t count) {
    const uint8_t *bytes = data;
    for (size_t i = 0u; i < count; ++i) hash_byte(hash, bytes[i]);
}

static uint64_t digest_rom(const uint8_t *rom, size_t size) {
    uint64_t hash = PARTITION_FNV_OFFSET;
    if (rom != NULL) hash_bytes(&hash, rom, size);
    hash_u64(&hash, size);
    return hash;
}

static void make_partition_rom(uint8_t rom[32768], const partition_scenario *scenario) {
    memset(rom, 0, 32768u);
    rom[0x143u] = 0xC0u;
    rom[0x147u] = 0x00u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x00u;

    size_t pc = 0x100u;
    for (unsigned i = 0u; i < PARTITION_PREFIX_NOPS; ++i) rom[pc++] = 0x00u;
    rom[pc++] = 0x3Eu; rom[pc++] = 0x01u;       /* LD A,1 */
    rom[pc++] = 0xE0u; rom[pc++] = 0x4Du;       /* LDH (KEY1),A */
    if (scenario->ime_on_at_stop != 0u) rom[pc++] = 0xFBu; /* EI; STOP */
    rom[pc++] = 0x10u; rom[pc++] = 0x00u;
    rom[pc++] = 0x76u;                           /* HALT after STOP */
    rom[pc++] = 0x18u; rom[pc++] = 0xFEu;

    /* Natural interrupt entry lands here; the handler disables IE before RETI. */
    const uint8_t timer_handler[] = {
        0xF3u, 0x3Eu, 0x00u, 0xEAu, 0xFFu, 0xFFu,
        0x3Eu, 0x55u, 0xEAu, 0x02u, 0xC0u, 0xD9u
    };
    memcpy(rom + 0x50u, timer_handler, sizeof(timer_handler));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static uint64_t half_dots_per_m(unsigned double_speed) {
    return (uint64_t)GBB_T_PER_M *
        (double_speed ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL);
}

static size_t partition_stop_pc(const partition_scenario *scenario) {
    return 0x100u + PARTITION_PREFIX_NOPS + 4u + scenario->ime_on_at_stop;
}

static uint64_t partition_pre_stop_half_dots(const partition_scenario *scenario) {
    return ((uint64_t)PARTITION_PREFIX_NOPS + 5u + scenario->ime_on_at_stop) *
        half_dots_per_m(scenario->start_double);
}

static unsigned partition_stop_case(const partition_scenario *scenario) {
    if (scenario->held_button != 0u) return scenario->pending_case != 0u ? 2u : 1u;
    if (scenario->pending_case != 0u) return 3u;
    return 4u;
}

static uint64_t partition_stop_retire_half_dots(const partition_scenario *scenario) {
    const uint64_t cost = partition_stop_case(scenario) == 4u
        ? (uint64_t)GBB_STOP_SWITCH_COST_HALF_DOTS >> scenario->start_double
        : half_dots_per_m(scenario->start_double);
    return partition_pre_stop_half_dots(scenario) + cost;
}

static uint64_t partition_stall_half_dots(const partition_scenario *scenario) {
    if (scenario->seeded_stall_half_dots != 0u) return scenario->seeded_stall_half_dots;
    const unsigned destination_double = scenario->start_double == 0u;
    return (uint64_t)GBB_SPEED_SWITCH_STALL_T *
        (destination_double ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL);
}

static uint64_t partition_stall_tail(const partition_scenario *scenario,
                                     uint64_t stall_start) {
    const unsigned destination_double = scenario->start_double == 0u;
    if (destination_double) return 0u;
    return ((stall_start + partition_stall_half_dots(scenario)) & 7u) == 4u ? 4u : 0u;
}

static int partition_meter_add(partition_meter *meter, uint64_t amount) {
    if (amount > GBB_PARTITION_CASE_HALF_DOT_CAP - meter->consumed_half_dots) {
        fputs("partition-cap-exceeded\n", stderr);
        return 1;
    }
    meter->consumed_half_dots += amount;
    return 0;
}

static int partition_append_audio(partition_streams *streams,
                                  const gbb_audio_frame *frames, size_t count) {
    if (count > PARTITION_PCM_CAPACITY - streams->pcm_count) {
        fputs("partition-pcm-cap-exceeded\n", stderr);
        return 1;
    }
    memcpy(streams->pcm + streams->pcm_count, frames, count * sizeof(*frames));
    streams->pcm_count += count;
    return 0;
}

static int partition_capture_serial_start(gbb_instance *machine,
                                          partition_streams *streams) {
    if (machine->serial_active && !streams->serial_tracking) {
        if (streams->serial_count == PARTITION_SERIAL_CAPACITY) {
            fputs("partition-serial-cap-exceeded\n", stderr);
            return 1;
        }
        streams->serial_output[streams->serial_count++] = machine->serial_data;
        streams->serial_tracking = 1u;
    }
    return 0;
}

static int partition_run_budget(partition_machine *run, uint64_t budget,
                                partition_meter *meter, int expected_terminal,
                                gbb_run_result *out_result) {
    gbb_audio_frame frames[PARTITION_PCM_CAPACITY];
    size_t frame_count = 0u;
    if (partition_capture_serial_start(run->machine, &run->streams) != 0) return 1;
    gbb_run_result result = gbb_run_audio(run->machine, budget, frames,
        sizeof(frames) / sizeof(frames[0]), &frame_count);
    if (result.reason != GBB_STOP_BUDGET && result.reason != expected_terminal) {
        fprintf(stderr, "partition-run-reason reason=%u consumed=%" PRIu64 " budget=%" PRIu64 "\n",
                (unsigned)result.reason, result.consumed_half_dots, budget);
        return 1;
    }
    if (partition_meter_add(meter, result.consumed_half_dots) != 0) return 1;
    if (partition_append_audio(&run->streams, frames, frame_count) != 0) return 1;
    if (!run->machine->serial_active) run->streams.serial_tracking = 0u;
    if (out_result != NULL) *out_result = result;
    return 0;
}

static int partition_machine_create(const partition_scenario *scenario,
                                    partition_machine *out) {
    uint8_t rom[32768];
    make_partition_rom(rom, scenario);
    memset(out, 0, sizeof(*out));
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &out->machine) != GBB_OK) return 1;
    if (gbb_load_rom(out->machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(out->machine);
        out->machine = NULL;
        return 1;
    }
    out->machine->pc = 0x100u;
    out->machine->double_speed = (uint8_t)scenario->start_double;
    out->machine->joypad_select = 0x20u;
    out->machine->serial_data = 0xA5u;
    out->machine->serial_control = 0x81u;
    out->machine->serial_bits = 0u;
    out->machine->serial_edge_remaining = 512u;
    out->machine->serial_active = 1;
    /* Keep DMA idle while the guest reaches STOP; seeded in-flight DMA is added at a prefix. */
    out->machine->ime = 0;
    out->machine->ime_delay = 0u;
    if (scenario->pending_case != 0u) {
        out->machine->ie = scenario->held_button != 0u ? 0x01u : 0x04u;
        out->machine->interrupt_flags = scenario->held_button != 0u ? 0x01u : 0x04u;
    }
    if (scenario->lcd_off != 0u) write8(out->machine, 0xFF40u, 0u);
    if (scenario->held_button != 0u || scenario->button_at_half_dots != 0u) {
        const gbb_input_event event = {
            scenario->held_button != 0u ? 0u : scenario->button_at_half_dots,
            GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_RIGHT
        };
        if (gbb_queue_events(out->machine, &event, 1u) != GBB_OK) {
            gbb_destroy(out->machine);
            out->machine = NULL;
            return 1;
        }
        if (scenario->button_at_half_dots != 0u) out->machine->ie |= 0x10u;
    }
    return 0;
}

static void partition_machine_destroy(partition_machine *run) {
    if (run->machine != NULL) gbb_destroy(run->machine);
    run->machine = NULL;
}

static int partition_prepare_stall(partition_machine *run,
                                   const partition_scenario *scenario,
                                   partition_meter *meter) {
    const uint64_t start_time = partition_stop_retire_half_dots(scenario);
    gbb_run_result result;
    if (partition_run_budget(run, start_time, meter, GBB_STOP_HALTED_IDLE, &result) != 0)
        return 1;
    if (result.consumed_half_dots != start_time ||
        run->machine->cpu_stall_kind != GBB_STALL_SPEED_SWITCH ||
        run->machine->cpu_stall_half_dots == 0u ||
        run->machine->pc != partition_stop_pc(scenario) + 2u) {
        fprintf(stderr, "partition-stall-setup time=%" PRIu64 " consumed=%" PRIu64 " reason=%u kind=%u remaining=%u pc=%04x expected=%04x mode=%u key1=%u flags=%02x ie=%02x if=%02x ime=%u delay=%u\n",
                run->machine->time_half_dots, result.consumed_half_dots, (unsigned)result.reason,
                (unsigned)run->machine->cpu_stall_kind,
                run->machine->cpu_stall_half_dots, run->machine->pc,
                (unsigned)(partition_stop_pc(scenario) + 2u), run->machine->exec_mode,
                run->machine->key1_armed, run->machine->cgb_flag, run->machine->ie,
                run->machine->interrupt_flags, (unsigned)run->machine->ime,
                run->machine->ime_delay);
        return 1;
    }
    if (scenario->timer_irq_in_stall != 0u) {
        /* A real reload edge raises IF from advance_devices inside the stall. */
        run->machine->ie |= 0x04u;
        run->machine->ime = 1;
        run->machine->tma = 0x00u;
        run->machine->tima = 0x00u;
        run->machine->tac = 0u;
        run->machine->timer_signal = 0;
        run->machine->timer_reload_pending = 1;
        run->machine->timer_reload_remaining = 96u;
    }
    if (scenario->seeded_stall_half_dots != 0u)
        run->machine->cpu_stall_half_dots = scenario->seeded_stall_half_dots;
    return 0;
}

static void partition_hash_instance(uint64_t *hash, const gbb_instance *machine,
                                    const partition_streams *streams) {
    gbb_trace_record cpu;
    memset(&cpu, 0, sizeof(cpu));
    gbb_test_cpu_snapshot(machine, &cpu);
    hash_u64(hash, cpu.time_half_dots);
    hash_u16(hash, cpu.pc);
    hash_byte(hash, cpu.opcode_size);
    hash_bytes(hash, cpu.opcode, sizeof(cpu.opcode));
    hash_byte(hash, cpu.a); hash_byte(hash, cpu.f); hash_byte(hash, cpu.b); hash_byte(hash, cpu.c);
    hash_byte(hash, cpu.d); hash_byte(hash, cpu.e); hash_byte(hash, cpu.h); hash_byte(hash, cpu.l);
    hash_u16(hash, cpu.sp);

    hash_u64(hash, machine->time_half_dots);
    hash_u64(hash, digest_rom(machine->rom, machine->rom_size));
    hash_byte(hash, machine->double_speed);
    hash_byte(hash, machine->cpu_stall_kind);
    hash_u32(hash, machine->cpu_stall_half_dots);
    hash_byte(hash, machine->stop_switch_pending);
    hash_byte(hash, machine->ime_delay);
    hash_byte(hash, (uint8_t)machine->ime);
    hash_byte(hash, (uint8_t)machine->halted);
    hash_byte(hash, (uint8_t)machine->stopped);
    hash_byte(hash, (uint8_t)machine->halt_bug);
    hash_byte(hash, (uint8_t)machine->locked);
    hash_u16(hash, machine->divider_counter);
    hash_byte(hash, machine->divider_phase);
    hash_byte(hash, machine->div);
    hash_byte(hash, machine->tima);
    hash_byte(hash, machine->tma);
    hash_byte(hash, machine->tac);
    hash_byte(hash, (uint8_t)machine->timer_signal);
    hash_byte(hash, (uint8_t)machine->timer_reload_pending);
    hash_byte(hash, machine->timer_reload_remaining);
    hash_u64(hash, machine->timer_reloaded_at);
    hash_byte(hash, machine->serial_data);
    hash_byte(hash, machine->serial_control);
    hash_byte(hash, machine->serial_bits);
    hash_byte(hash, (uint8_t)machine->serial_active);
    hash_u16(hash, machine->serial_edge_remaining);
    hash_byte(hash, machine->dma_register);
    hash_byte(hash, machine->dma_page);
    hash_byte(hash, machine->dma_pending_page);
    hash_byte(hash, machine->dma_index);
    hash_byte(hash, machine->dma_phase);
    hash_byte(hash, (uint8_t)machine->dma_active);
    hash_byte(hash, (uint8_t)machine->dma_start_pending);
    hash_byte(hash, (uint8_t)machine->dma_cpu_blocked);

    hash_u16(hash, machine->ppu_dot);
    hash_byte(hash, machine->ppu_half_phase);
    hash_byte(hash, machine->ppu_mode);
    hash_byte(hash, machine->ppu_stat_line);
    hash_byte(hash, machine->ppu_fetch_stage);
    hash_byte(hash, machine->ppu_fetch_phase);
    hash_u16(hash, machine->ppu_fetch_enqueued);
    hash_byte(hash, machine->ppu_transfer_age);
    hash_byte(hash, machine->ppu_output_x);
    hash_byte(hash, machine->ppu_scroll_discard);
    hash_byte(hash, machine->ppu_fine_scroll);
    hash_byte(hash, machine->ppu_mode3_stall);
    hash_byte(hash, machine->ppu_window_started);
    hash_byte(hash, machine->ppu_transfer_complete);
    hash_u16(hash, machine->ppu_objects_stalled);
    hash_u32(hash, machine->ppu_object_tiles_fetched);
    hash_byte(hash, machine->ppu_selected_object_count);
    hash_byte(hash, machine->ppu_scan_index);
    hash_byte(hash, machine->ppu_window_line);
    hash_byte(hash, machine->ppu_window_line_drawn);
    hash_bytes(hash, machine->ppu_fifo, sizeof(machine->ppu_fifo));
    hash_byte(hash, machine->ppu_fifo_head);
    hash_byte(hash, machine->ppu_fifo_count);
    hash_bytes(hash, machine->ppu_selected_objects, sizeof(machine->ppu_selected_objects));
    hash_bytes(hash, machine->ppu_selected_y, sizeof(machine->ppu_selected_y));
    hash_bytes(hash, machine->ppu_selected_x, sizeof(machine->ppu_selected_x));
    hash_bytes(hash, machine->ppu_selected_tile, sizeof(machine->ppu_selected_tile));
    hash_bytes(hash, machine->ppu_selected_attributes, sizeof(machine->ppu_selected_attributes));

    hash_byte(hash, machine->apu_sequencer_step);
    hash_u64(hash, machine->apu_sample_phase);
    hash_byte(hash, machine->apu_nr50);
    hash_byte(hash, machine->apu_nr51);
    hash_byte(hash, machine->apu_power);
    hash_byte(hash, machine->audio_event_head);
    for (size_t side = 0u; side < 2u; ++side) {
        hash_u32(hash, (uint32_t)machine->audio_mix_level[side]);
        hash_u64(hash, (uint64_t)machine->audio_hpf_input[side]);
        hash_u64(hash, (uint64_t)machine->audio_hpf_output[side]);
        for (size_t tap = 0u; tap < GBB_AUDIO_EVENT_TAPS; ++tap)
            hash_u64(hash, (uint64_t)machine->audio_event_ring[side][tap]);
    }

    hash_byte(hash, machine->cart.rtc_s);
    hash_byte(hash, machine->cart.rtc_m);
    hash_byte(hash, machine->cart.rtc_h);
    hash_byte(hash, machine->cart.rtc_dl);
    hash_byte(hash, machine->cart.rtc_dh);
    hash_bytes(hash, machine->cart.rtc_l, sizeof(machine->cart.rtc_l));
    hash_byte(hash, machine->cart.rtc_latch_prev);
    hash_u32(hash, machine->cart.rtc_sub);
    hash_u64(hash, machine->cart.rtc_synced_at);

    hash_byte(hash, read8(machine, 0xFF0Fu));
    hash_byte(hash, read8(machine, 0xFF4Du));
    hash_byte(hash, read8(machine, 0xFF04u));
    hash_byte(hash, read8(machine, 0xFF05u));
    hash_byte(hash, read8(machine, 0xFF44u));
    hash_byte(hash, read8(machine, 0xFF41u));

    hash_bytes(hash, machine->wram, sizeof(machine->wram));
    hash_bytes(hash, machine->hram, sizeof(machine->hram));
    hash_bytes(hash, machine->vram, sizeof(machine->vram));
    hash_bytes(hash, machine->oam, sizeof(machine->oam));
    hash_bytes(hash, machine->bg_cram, sizeof(machine->bg_cram));
    hash_bytes(hash, machine->obj_cram, sizeof(machine->obj_cram));
    for (size_t pixel = 0u; pixel < GBB_FRAME_PIXELS; ++pixel) {
        hash_u16(hash, machine->rgb_working[pixel]);
        hash_u16(hash, machine->rgb_completed[pixel]);
    }
    hash_u64(hash, machine->frame_generation);
    hash_u64(hash, machine->frame_completion_half_dots);

    hash_u64(hash, streams->pcm_count);
    for (size_t i = 0u; i < streams->pcm_count; ++i) {
        hash_u16(hash, (uint16_t)streams->pcm[i].left);
        hash_u16(hash, (uint16_t)streams->pcm[i].right);
    }
    hash_u64(hash, streams->serial_count);
    hash_bytes(hash, streams->serial_output, streams->serial_count);
}

static uint64_t partition_digest(const gbb_instance *machine,
                                 const partition_streams *streams) {
    uint64_t hash = PARTITION_FNV_OFFSET;
    partition_hash_instance(&hash, machine, streams);
    return hash;
}

static int partition_run_reference(const partition_scenario *scenario,
                                   uint64_t total_half_dots,
                                   partition_meter *meter, uint64_t *digest) {
    partition_machine run;
    REQUIRE(partition_machine_create(scenario, &run) == 0);
    if (scenario->prepare_at_stall != 0u &&
        partition_prepare_stall(&run, scenario, meter) != 0) {
        partition_machine_destroy(&run);
        return 1;
    }
    gbb_run_result result;
    if (partition_run_budget(&run, total_half_dots, meter, GBB_STOP_HALTED_IDLE,
                             &result) != 0) {
        partition_machine_destroy(&run);
        return 1;
    }
    if (result.consumed_half_dots != total_half_dots &&
        result.reason != GBB_STOP_HALTED_IDLE) {
        fprintf(stderr, "partition-reference-progress consumed=%" PRIu64 " total=%" PRIu64 "\n",
                result.consumed_half_dots, total_half_dots);
        partition_machine_destroy(&run);
        return 1;
    }
    if (result.consumed_half_dots == 0u || result.consumed_half_dots > total_half_dots) {
        fputs("partition-reference-invalid-progress\n", stderr);
        partition_machine_destroy(&run);
        return 1;
    }
    *digest = partition_digest(run.machine, &run.streams);
    partition_machine_destroy(&run);
    return 0;
}

static int partition_run_cut(const partition_scenario *scenario,
                             const uint64_t *cuts, size_t cut_count,
                             uint64_t total_half_dots, partition_meter *meter,
                             uint64_t *digest) {
    partition_machine run;
    REQUIRE(partition_machine_create(scenario, &run) == 0);
    if (scenario->prepare_at_stall != 0u &&
        partition_prepare_stall(&run, scenario, meter) != 0) {
        partition_machine_destroy(&run);
        return 1;
    }
    uint64_t previous = 0u;
    uint64_t pending_budget = 0u;
    uint64_t consumed_total = 0u;
    int terminal = 0;
    for (size_t i = 0u; i < cut_count; ++i) {
        if (cuts[i] < previous || cuts[i] > total_half_dots) {
            fprintf(stderr, "partition-cut-order cut=%" PRIu64 " previous=%" PRIu64 "\n",
                    cuts[i], previous);
            partition_machine_destroy(&run);
            return 1;
        }
        pending_budget += cuts[i] - previous;
        previous = cuts[i];
        if (pending_budget != 0u) {
            gbb_run_result result;
            if (partition_run_budget(&run, pending_budget, meter,
                                     GBB_STOP_HALTED_IDLE, &result) != 0) {
                partition_machine_destroy(&run);
                return 1;
            }
            pending_budget -= result.consumed_half_dots;
            consumed_total += result.consumed_half_dots;
            if (result.reason == GBB_STOP_HALTED_IDLE) {
                terminal = 1;
                break;
            }
        }
    }
    if (!terminal) pending_budget += total_half_dots - previous;
    if (!terminal && pending_budget != 0u) {
        gbb_run_result result;
        if (partition_run_budget(&run, pending_budget, meter,
                                 GBB_STOP_HALTED_IDLE, &result) != 0) {
            partition_machine_destroy(&run);
            return 1;
        }
        pending_budget -= result.consumed_half_dots;
        consumed_total += result.consumed_half_dots;
        terminal = result.reason == GBB_STOP_HALTED_IDLE;
    }
    if ((!terminal && pending_budget != 0u) || consumed_total == 0u ||
        consumed_total > total_half_dots ||
        (!terminal && consumed_total != total_half_dots)) {
        fprintf(stderr, "partition-cut-progress consumed=%" PRIu64 " pending=%" PRIu64
                        " total=%" PRIu64 "\n", consumed_total, pending_budget,
                total_half_dots);
        partition_machine_destroy(&run);
        return 1;
    }
    *digest = partition_digest(run.machine, &run.streams);
    partition_machine_destroy(&run);
    return 0;
}

static int partition_compare_one_cut(const partition_scenario *scenario,
                                     uint64_t cut, uint64_t total,
                                     uint64_t reference, partition_meter *meter,
                                     const char *name) {
    uint64_t actual = 0u;
    if (partition_run_cut(scenario, &cut, 1u, total, meter, &actual) != 0) return 1;
    if (actual != reference) {
        fprintf(stderr, "partition-mismatch scenario=%s cut=%" PRIu64
                        " reference=%016" PRIx64 " actual=%016" PRIx64 "\n",
                name, cut, reference, actual);
        return 1;
    }
    return 0;
}

static int cgb_partition_stall_start_window(void) {
    partition_scenario scenario = {0};
    const uint64_t stall_start = partition_stop_retire_half_dots(&scenario);
    const uint64_t total = stall_start + 4096u;
    partition_meter meter = {0};
    uint64_t reference = 0u;
    REQUIRE(partition_run_reference(&scenario, total, &meter, &reference) == 0);
    for (int offset = -64; offset <= 64; ++offset) {
        const uint64_t cut = (uint64_t)((int64_t)stall_start + offset);
        REQUIRE(partition_compare_one_cut(&scenario, cut, total, reference, &meter,
                                          "cgb_partition_stall_start_window") == 0);
    }
    printf("cgb_partition_stall_start_window pass emulated_half_dots=%" PRIu64 "\n",
           meter.consumed_half_dots);
    return 0;
}

static int cgb_partition_hostile_irq_in_stall(void) {
    partition_scenario scenario = {0};
    scenario.prepare_at_stall = 1u;
    scenario.timer_irq_in_stall = 1u;
    const uint64_t irq_half_dots = 96u;
    const uint64_t total = irq_half_dots + 4096u;
    partition_meter meter = {0};
    uint64_t reference = 0u;
    REQUIRE(partition_run_reference(&scenario, total, &meter, &reference) == 0);
    for (int offset = -64; offset <= 64; ++offset) {
        const uint64_t cut = (uint64_t)((int64_t)irq_half_dots + offset);
        REQUIRE(partition_compare_one_cut(&scenario, cut, total, reference, &meter,
                                          "cgb_partition_hostile_irq_in_stall") == 0);
    }
    printf("cgb_partition_hostile_irq_in_stall pass emulated_half_dots=%" PRIu64 "\n",
           meter.consumed_half_dots);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
#ifdef GBB_P12_MUTANT_BUILD
    if (argc >= 4 && strcmp(argv[argc - 2], "--mutants") == 0) {
        char *end = NULL;
        errno = 0;
        unsigned long long mask = strtoull(argv[argc - 1], &end, 0);
        if (errno != 0 || end == argv[argc - 1] || *end != '\0') return 2;
        gbb_p12_mutants = (uint64_t)mask;
        argc -= 2;
    }
#else
    for (int i = 2; i < argc; ++i)
        if (strcmp(argv[i], "--mutants") == 0) return 2;
#endif
    if (strcmp(argv[1], "cgb_partition_stall_start_window") == 0)
        return cgb_partition_stall_start_window();
    if (strcmp(argv[1], "cgb_partition_hostile_irq_in_stall") == 0)
        return cgb_partition_hostile_irq_in_stall();
    return 2;
}
