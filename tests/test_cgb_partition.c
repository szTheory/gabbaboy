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
    unsigned ime_pre_enabled_before_stop;
    unsigned held_button;
    unsigned lcd_off;
    unsigned prepare_at_stall;
    unsigned timer_irq_in_stall;
    unsigned delayed_ime_timer_guest;
    unsigned switch_count;
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

typedef struct {
    gbb_instance *machine_image;
    uint8_t *cartridge_ram;
    size_t cartridge_ram_size;
    size_t rom_size;
    uint64_t rom_digest;
    partition_streams streams;
} partition_snap;

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
    rom[0x147u] = 0x02u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;

    size_t pc = 0x100u;
    for (unsigned i = 0u; i < PARTITION_PREFIX_NOPS; ++i) rom[pc++] = 0x00u;
    rom[pc++] = 0x3Eu; rom[pc++] = 0x01u;       /* LD A,1 */
    rom[pc++] = 0xE0u; rom[pc++] = 0x4Du;       /* LDH (KEY1),A */
    const unsigned switch_count = scenario->switch_count != 0u ? scenario->switch_count : 1u;
    for (unsigned stop = 0u; stop < switch_count; ++stop) {
        if (stop != 0u) {
            rom[pc++] = 0x3Eu; rom[pc++] = 0x01u;
            rom[pc++] = 0xE0u; rom[pc++] = 0x4Du;
        }
        if (stop == 0u && scenario->ime_pre_enabled_before_stop != 0u) {
            rom[pc++] = 0xFBu; rom[pc++] = 0x00u; /* EI; NOP makes IME live before STOP. */
        } else if (stop == 0u && scenario->ime_on_at_stop != 0u) {
            rom[pc++] = 0xFBu;
        }
        rom[pc++] = 0x10u; rom[pc++] = 0x00u;
    }
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

/* Mirrors the 12-06 regression guest: it raises timer IF under DI, disables
 * further requests, arms KEY1, and retires EI immediately before STOP. */
static void make_delayed_ime_timer_rom(uint8_t rom[32768]) {
    static const uint8_t code[] = {
        0x06u,0x00u,                         /* LD B,0 */
        0x3Eu,0x04u,0xEAu,0xFFu,0xFFu,       /* IE = timer */
        0x3Eu,0x00u,0xE0u,0x0Fu,             /* IF = 0 */
        0x3Eu,0xFFu,0xE0u,0x05u,             /* TIMA = FF */
        0x3Eu,0x00u,0xE0u,0x06u,             /* TMA = 0 */
        0x3Eu,0x05u,0xE0u,0x07u,             /* TAC = on, 16 T */
        0xF0u,0x0Fu,0xE6u,0x04u,0x28u,0xFAu, /* wait for IF.2 */
        0x3Eu,0x00u,0xE0u,0x07u,             /* stop further timer requests */
        0x3Eu,0x01u,0xE0u,0x4Du,             /* arm KEY1 */
        0xFBu,                               /* EI immediately before STOP */
        0x10u,0x04u,                         /* STOP; INC B */
        0x78u,0xEAu,0x00u,0xC0u,             /* store B */
        0x79u,0xEAu,0x01u,0xC0u,             /* store C from handler */
        0x18u,0xFEu                          /* stable loop */
    };
    memset(rom, 0, 32768u);
    rom[0x143u] = 0xC0u;
    rom[0x147u] = 0x02u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    memcpy(rom + 0x100u, code, sizeof(code));
    rom[0x50u] = 0x0Eu; rom[0x51u] = 0x42u; rom[0x52u] = 0xD9u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static uint64_t half_dots_per_m(unsigned double_speed) {
    return (uint64_t)GBB_T_PER_M *
        (double_speed ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL);
}

static size_t partition_stop_pc(const partition_scenario *scenario, unsigned stop_index) {
    return 0x100u + PARTITION_PREFIX_NOPS + 4u + scenario->ime_on_at_stop +
        2u * scenario->ime_pre_enabled_before_stop +
        (size_t)stop_index * 6u;
}

static uint64_t partition_pre_stop_half_dots(const partition_scenario *scenario) {
    /* NOP prefix, LD A,1 (2 M), LDH (KEY1),A (3 M), then optional EI. */
    return ((uint64_t)PARTITION_PREFIX_NOPS + 5u + scenario->ime_on_at_stop +
        2u * scenario->ime_pre_enabled_before_stop) *
        half_dots_per_m(scenario->start_double);
}

static unsigned partition_stop_case(const partition_scenario *scenario) {
    if (scenario->held_button != 0u) return scenario->pending_case != 0u ? 2u : 1u;
    if (scenario->pending_case != 0u) return 3u;
    return 4u;
}

static uint64_t partition_stop_retire_half_dots(const partition_scenario *scenario) {
    const unsigned selected = partition_stop_case(scenario);
    const uint64_t cost = selected == 3u || selected == 4u
        ? (uint64_t)GBB_STOP_SWITCH_COST_HALF_DOTS >> scenario->start_double
        : half_dots_per_m(scenario->start_double);
    return partition_pre_stop_half_dots(scenario) + cost;
}

static uint64_t partition_stop_retire_at(const partition_scenario *scenario,
                                         unsigned stop_index) {
    uint64_t time = partition_pre_stop_half_dots(scenario);
    unsigned speed = scenario->start_double;
    for (unsigned stop = 0u; stop <= stop_index; ++stop) {
        if (stop != 0u) time += 5u * half_dots_per_m(speed);
        const unsigned selected = stop == 0u ? partition_stop_case(scenario) : 4u;
        time += selected == 3u || selected == 4u
            ? (uint64_t)GBB_STOP_SWITCH_COST_HALF_DOTS >> speed
            : half_dots_per_m(speed);
        if (stop < stop_index) {
            speed ^= 1u;
            const uint64_t stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
                (speed != 0u ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL);
            time += stall;
            if (speed == 0u && (time & 7u) == 4u) time += 4u;
        }
    }
    return time;
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
    if (scenario->delayed_ime_timer_guest != 0u)
        make_delayed_ime_timer_rom(rom);
    else
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
    if (scenario->delayed_ime_timer_guest != 0u) {
        out->machine->ie = 0u;
        out->machine->interrupt_flags = 0u;
        out->machine->serial_data = 0u;
        out->machine->serial_control = 0u;
        out->machine->serial_bits = 0u;
        out->machine->serial_edge_remaining = 0u;
        out->machine->serial_active = 0;
    } else if (scenario->pending_case != 0u) {
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

static void partition_snapshot_destroy(partition_snap *snapshot) {
    free(snapshot->machine_image);
    free(snapshot->cartridge_ram);
    memset(snapshot, 0, sizeof(*snapshot));
}

static int partition_snapshot(const partition_machine *src, partition_snap *out) {
    if (src == NULL || src->machine == NULL || out == NULL) return 1;
    const gbb_instance *machine = src->machine;
#define REJECT_UNSUPPORTED(field) do { \
    if (machine->field != NULL) { \
        fprintf(stderr, "partition-snapshot-unsupported %s\n", #field); \
        return 1; \
    } \
} while (0)
    REJECT_UNSUPPORTED(test_events);
    REJECT_UNSUPPORTED(test_ppu_events);
    REJECT_UNSUPPORTED(test_dma_events);
    REJECT_UNSUPPORTED(diagnostic_output);
    REJECT_UNSUPPORTED(diagnostic_operation);
#undef REJECT_UNSUPPORTED
    if (machine->rom == NULL ||
        (machine->cartridge_ram_size != 0u && machine->cartridge_ram == NULL)) {
        fputs("partition-snapshot-invalid-owned-buffer\n", stderr);
        return 1;
    }
    memset(out, 0, sizeof(*out));
    out->machine_image = malloc(sizeof(*out->machine_image));
    if (out->machine_image == NULL) return 1;
    if (machine->cartridge_ram_size != 0u) {
        out->cartridge_ram = malloc(machine->cartridge_ram_size);
        if (out->cartridge_ram == NULL) {
            partition_snapshot_destroy(out);
            return 1;
        }
        memcpy(out->cartridge_ram, machine->cartridge_ram, machine->cartridge_ram_size);
    }
    *out->machine_image = *machine;
    out->machine_image->rom = NULL;
    out->machine_image->cartridge_ram = NULL;
    out->machine_image->audio_frames = NULL;
    out->machine_image->audio_frame_capacity = 0u;
    out->machine_image->audio_frame_count = 0u;
    out->machine_image->audio_run_active = 0;
    out->cartridge_ram_size = machine->cartridge_ram_size;
    out->rom_size = machine->rom_size;
    out->rom_digest = digest_rom(machine->rom, machine->rom_size);
    out->streams = src->streams;
    return 0;
}

static int partition_restore(partition_machine *dst, const partition_snap *snapshot) {
    if (dst == NULL || dst->machine == NULL || snapshot == NULL ||
        snapshot->machine_image == NULL) return 1;
    gbb_instance *machine = dst->machine;
    uint8_t *const rom = machine->rom;
    const size_t rom_size = machine->rom_size;
    uint8_t *const cartridge_ram = machine->cartridge_ram;
    const size_t cartridge_ram_size = machine->cartridge_ram_size;
    if (rom == NULL || rom_size != snapshot->rom_size ||
        digest_rom(rom, rom_size) != snapshot->rom_digest ||
        cartridge_ram_size != snapshot->cartridge_ram_size ||
        (cartridge_ram_size != 0u &&
         (cartridge_ram == NULL || snapshot->cartridge_ram == NULL))) {
        fputs("partition-snapshot-restore-identity-fail\n", stderr);
        return 1;
    }
    *machine = *snapshot->machine_image;
    machine->rom = rom;
    machine->cartridge_ram = cartridge_ram;
    machine->audio_frames = NULL;
    machine->audio_frame_capacity = 0u;
    machine->audio_frame_count = 0u;
    machine->audio_run_active = 0;
    if (cartridge_ram_size != 0u)
        memcpy(cartridge_ram, snapshot->cartridge_ram, cartridge_ram_size);
    dst->streams = snapshot->streams;
    return 0;
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
        run->machine->pc != partition_stop_pc(scenario, 0u) + 2u) {
        fprintf(stderr, "partition-stall-setup time=%" PRIu64 " consumed=%" PRIu64 " reason=%u kind=%u remaining=%u pc=%04x expected=%04x mode=%u key1=%u flags=%02x ie=%02x if=%02x ime=%u delay=%u\n",
                run->machine->time_half_dots, result.consumed_half_dots, (unsigned)result.reason,
                (unsigned)run->machine->cpu_stall_kind,
                run->machine->cpu_stall_half_dots, run->machine->pc,
                (unsigned)(partition_stop_pc(scenario, 0u) + 2u), run->machine->exec_mode,
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

    hash_byte(hash, machine->hdma.mode);
    hash_byte(hash, machine->hdma.active);
    hash_byte(hash, machine->hdma.pending_hblank);
    hash_u16(hash, machine->hdma.blocks_remaining);
    hash_byte(hash, machine->hdma.byte_index);
    hash_byte(hash, machine->hdma.byte_phase);
    hash_u16(hash, machine->hdma.source_cursor);
    hash_u32(hash, machine->hdma.destination_cursor);
    hash_byte(hash, machine->hdma.block_vram_bank);
    hash_byte(hash, machine->hdma.source_high);
    hash_byte(hash, machine->hdma.source_low);
    hash_byte(hash, machine->hdma.destination_high);
    hash_byte(hash, machine->hdma.destination_low);
    hash_byte(hash, machine->hdma.control_readback);

    hash_byte(hash, machine->cart.kind);
    hash_byte(hash, machine->cart.ram_window_mapped);
    hash_byte(hash, machine->cart.rom_bank_lo);
    hash_byte(hash, machine->cart.rom_bank_hi);
    hash_byte(hash, machine->cart.ram_bank);
    hash_byte(hash, machine->cart.ram_enabled);
    hash_byte(hash, machine->cart.mbc1_mode);
    hash_byte(hash, machine->cart.rumble_on);
    hash_u64(hash, machine->cart.rumble_changes);

    hash_u64(hash, machine->input_event_count);
    for (size_t i = 0u; i < machine->input_event_count; ++i) {
        hash_u64(hash, machine->input_events[i].at_half_dots);
        hash_byte(hash, (uint8_t)machine->input_events[i].kind);
        hash_byte(hash, machine->input_events[i].value);
    }

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
    hash_u64(hash, machine->cartridge_ram_size);
    if (machine->cartridge_ram_size != 0u)
        hash_bytes(hash, machine->cartridge_ram, machine->cartridge_ram_size);
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

static int partition_run_cut_instance(partition_machine *run,
                                      const uint64_t *cuts, size_t cut_count,
                                      uint64_t total_half_dots, partition_meter *meter,
                                      uint64_t *digest) {
    uint64_t previous = 0u;
    uint64_t pending_budget = 0u;
    uint64_t consumed_total = 0u;
    int terminal = 0;
    for (size_t i = 0u; i < cut_count; ++i) {
        if (cuts[i] < previous || cuts[i] > total_half_dots) {
            fprintf(stderr, "partition-cut-order cut=%" PRIu64 " previous=%" PRIu64 "\n",
                    cuts[i], previous);
            return 1;
        }
        pending_budget += cuts[i] - previous;
        previous = cuts[i];
        if (pending_budget != 0u) {
            gbb_run_result result;
            if (partition_run_budget(run, pending_budget, meter,
                                     GBB_STOP_HALTED_IDLE, &result) != 0) {
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
        if (partition_run_budget(run, pending_budget, meter,
                                 GBB_STOP_HALTED_IDLE, &result) != 0) {
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
        return 1;
    }
    *digest = partition_digest(run->machine, &run->streams);
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
    const int result = partition_run_cut_instance(&run, cuts, cut_count,
        total_half_dots, meter, digest);
    partition_machine_destroy(&run);
    return result;
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

static int partition_compare_snapshot_cut(const partition_scenario *scenario,
                                          const partition_snap *snapshot,
                                          uint64_t cut, uint64_t total,
                                          uint64_t reference, partition_meter *meter,
                                          const char *name) {
    partition_machine run;
    partition_scenario continuation = *scenario;
    continuation.prepare_at_stall = 0u;
    REQUIRE(partition_machine_create(&continuation, &run) == 0);
    if (partition_restore(&run, snapshot) != 0) {
        partition_machine_destroy(&run);
        return 1;
    }
    uint64_t actual = 0u;
    if (partition_run_cut_instance(&run, &cut, 1u, total, meter, &actual) != 0) {
        partition_machine_destroy(&run);
        return 1;
    }
    partition_machine_destroy(&run);
    if (actual != reference) {
        fprintf(stderr, "partition-mismatch scenario=%s cut=%" PRIu64
                        " reference=%016" PRIx64 " actual=%016" PRIx64 "\n",
                name, cut, reference, actual);
        return 1;
    }
    return 0;
}

static int partition_measure_stop_retire(const partition_scenario *scenario,
                                         unsigned stop_index, partition_meter *meter,
                                         uint64_t *measured) {
    partition_machine probe;
    if (partition_machine_create(scenario, &probe) != 0) return 1;
    const size_t target_pc = partition_stop_pc(scenario, stop_index);
    unsigned steps = 0u;
    while (steps++ < 256u) {
        const int pending_interrupt = probe.machine->ime != 0 &&
            (probe.machine->ie & probe.machine->interrupt_flags & 0x1Fu) != 0u;
        if (probe.machine->pc == target_pc && !pending_interrupt) {
            decoded instruction = decode(probe.machine);
            const uint8_t cost = instruction_cost(probe.machine, instruction);
            gbb_run_result result;
            if (partition_run_budget(&probe, cost, meter, GBB_STOP_HALTED_IDLE,
                                     &result) != 0 || result.consumed_half_dots != cost) {
                partition_machine_destroy(&probe);
                return 1;
            }
            *measured = probe.machine->time_half_dots;
            partition_machine_destroy(&probe);
            return 0;
        }
        uint64_t budget = 0u;
        if (probe.machine->cpu_stall_kind != GBB_STALL_NONE) {
            budget = probe.machine->cpu_stall_half_dots;
        } else if (pending_interrupt) {
            budget = 40u >> probe.machine->double_speed;
        } else {
            decoded instruction = decode(probe.machine);
            if (!instruction.supported || instruction.ticks == 0u) {
                fputs("partition-stop-time-decode-fail\n", stderr);
                partition_machine_destroy(&probe);
                return 1;
            }
            budget = instruction_cost(probe.machine, instruction);
        }
        gbb_run_result result;
        if (partition_run_budget(&probe, budget, meter, GBB_STOP_HALTED_IDLE,
                                 &result) != 0 || result.consumed_half_dots != budget) {
            fputs("partition-stop-time-step-fail\n", stderr);
            partition_machine_destroy(&probe);
            return 1;
        }
    }
    fputs("partition-stop-time-not-reached\n", stderr);
    partition_machine_destroy(&probe);
    return 1;
}

static int partition_stall_end_window(const partition_scenario *scenario,
                                      uint64_t stall_half_dots, const char *name,
                                      partition_meter *meter) {
    partition_machine prefix;
    partition_snap snapshot = {0};
    partition_meter local_meter = {0};
    if (partition_machine_create(scenario, &prefix) != 0) return 1;
    const uint64_t stop_retire = partition_stop_retire_half_dots(scenario);
    const uint64_t tail = partition_stall_tail(scenario, stop_retire);
    if (stall_half_dots + tail < 128u) {
        partition_machine_destroy(&prefix);
        return 1;
    }
    const uint64_t prefix_to_anchor = stall_half_dots + tail - 128u;
    if (scenario->seeded_stall_half_dots != 0u &&
        partition_prepare_stall(&prefix, scenario, &local_meter) != 0) {
        partition_machine_destroy(&prefix);
        return 1;
    }
    const uint64_t run_to_anchor = scenario->seeded_stall_half_dots != 0u
        ? prefix_to_anchor : stop_retire + prefix_to_anchor;
    gbb_run_result prefix_result = {0};
    if (partition_run_budget(&prefix, run_to_anchor, &local_meter,
                             GBB_STOP_HALTED_IDLE, &prefix_result) != 0 ||
        prefix_result.consumed_half_dots != run_to_anchor ||
        prefix.machine->cpu_stall_kind == GBB_STALL_NONE) {
        partition_machine_destroy(&prefix);
        return 1;
    }
    if (partition_snapshot(&prefix, &snapshot) != 0) {
        partition_machine_destroy(&prefix);
        partition_snapshot_destroy(&snapshot);
        return 1;
    }
    const uint64_t total = 192u;
    gbb_run_result ref_result;
    if (partition_run_budget(&prefix, total, &local_meter, GBB_STOP_HALTED_IDLE,
                             &ref_result) != 0 || ref_result.consumed_half_dots == 0u) {
        partition_machine_destroy(&prefix);
        partition_snapshot_destroy(&snapshot);
        return 1;
    }
    const uint64_t reference = partition_digest(prefix.machine, &prefix.streams);
    for (int offset = -64; offset <= 64; ++offset) {
        const uint64_t cut = (uint64_t)(128 + offset);
        if (partition_compare_snapshot_cut(scenario, &snapshot, cut, total, reference,
                                           &local_meter, name) != 0) {
            partition_machine_destroy(&prefix);
            partition_snapshot_destroy(&snapshot);
            return 1;
        }
    }
    partition_machine_destroy(&prefix);
    partition_snapshot_destroy(&snapshot);
    *meter = local_meter;
    printf("%s pass cuts=129 emulated_half_dots=%" PRIu64 "\n",
           name, meter->consumed_half_dots);
    return 0;
}

static int cgb_partition_snapshot_fidelity(void) {
    partition_scenario scenario = {0};
    const uint64_t stall = partition_stall_half_dots(&scenario);
    const uint64_t stop_retire = partition_stop_retire_half_dots(&scenario);
    const uint64_t tail = partition_stall_tail(&scenario, stop_retire);
    const uint64_t stall_quantum = half_dots_per_m(scenario.start_double == 0u ? 1u : 0u);
    const uint64_t prefix_stall = (stall / 2u) / stall_quantum * stall_quantum;
    const uint64_t continuation = stall - prefix_stall + tail + 64u;
    partition_meter meter = {0};
    partition_machine prefix;
    partition_snap snapshot = {0};
    REQUIRE(partition_machine_create(&scenario, &prefix) == 0);
    REQUIRE(partition_prepare_stall(&prefix, &scenario, &meter) == 0);
    gbb_run_result at_mid_stall;
    REQUIRE(partition_run_budget(&prefix, prefix_stall, &meter,
                                 GBB_STOP_HALTED_IDLE, &at_mid_stall) == 0);
    REQUIRE(at_mid_stall.consumed_half_dots == prefix_stall);
    REQUIRE(partition_snapshot(&prefix, &snapshot) == 0);

    gbb_run_result baseline_result;
    REQUIRE(partition_run_budget(&prefix, continuation, &meter, GBB_STOP_HALTED_IDLE,
                                 &baseline_result) == 0);
    const uint64_t baseline = partition_digest(prefix.machine, &prefix.streams);

    partition_machine restored;
    REQUIRE(partition_machine_create(&scenario, &restored) == 0);
    /* A post-snapshot source mutation must not alias into the restored cartridge RAM. */
    REQUIRE(prefix.machine->cartridge_ram_size != 0u);
    prefix.machine->cartridge_ram[0] ^= 0x5Au;
    REQUIRE(partition_restore(&restored, &snapshot) == 0);
    gbb_run_result restored_result;
    REQUIRE(partition_run_budget(&restored, continuation, &meter, GBB_STOP_HALTED_IDLE,
                                 &restored_result) == 0);
    const uint64_t restored_digest = partition_digest(restored.machine, &restored.streams);
    REQUIRE(restored_digest == baseline);

    partition_scenario fresh_scenario = scenario;
    fresh_scenario.prepare_at_stall = 0u;
    uint64_t fresh_digest = 0u;
    REQUIRE(partition_run_reference(&fresh_scenario,
        stop_retire + stall + tail + 64u, &meter, &fresh_digest) == 0);
    REQUIRE(fresh_digest == baseline);

    partition_snap rejected = {0};
    gbb_diagnostic_record *saved_diagnostic = restored.machine->diagnostic_output;
    restored.machine->diagnostic_output = (gbb_diagnostic_record *)(uintptr_t)1u;
    REQUIRE(partition_snapshot(&restored, &rejected) != 0);
    restored.machine->diagnostic_output = saved_diagnostic;

    partition_machine_destroy(&restored);
    partition_machine_destroy(&prefix);
    partition_snapshot_destroy(&snapshot);
    printf("cgb_partition_snapshot_fidelity pass emulated_half_dots=%" PRIu64 "\n",
           meter.consumed_half_dots);
    return 0;
}

static int cgb_partition_stall_end_window_to_double(void) {
    partition_scenario scenario = {0};
    const uint64_t stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
        GBB_HALF_DOTS_PER_T_DOUBLE;
    partition_meter meter = {0};
    return partition_stall_end_window(&scenario, stall,
        "cgb_partition_stall_end_window_to_double", &meter);
}

static int cgb_partition_stall_end_window_to_normal(void) {
    partition_scenario scenario = {0};
    scenario.start_double = 1u;
    const uint64_t stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
        GBB_HALF_DOTS_PER_T_NORMAL;
    partition_meter meter = {0};
    return partition_stall_end_window(&scenario, stall,
        "cgb_partition_stall_end_window_to_normal", &meter);
}

static int cgb_partition_stall_end_window_seeded(void) {
    partition_scenario scenario = {0};
    scenario.seeded_stall_half_dots = 512u;
    partition_meter meter = {0};
    return partition_stall_end_window(&scenario, 512u,
        "cgb_partition_stall_end_window_seeded", &meter);
}

static int partition_stop_window(const partition_scenario *scenario,
                                 unsigned stop_index, const char *name,
                                 partition_meter *meter) {
    const uint64_t predicted_stop_retire = partition_stop_retire_at(scenario, stop_index);
    partition_meter local_meter = {0};
    uint64_t measured_stop_retire = 0u;
    if (partition_measure_stop_retire(scenario, stop_index, &local_meter,
                                      &measured_stop_retire) != 0 ||
        (scenario->ime_pre_enabled_before_stop == 0u &&
         measured_stop_retire != predicted_stop_retire)) {
        fprintf(stderr, "partition-stop-time-mismatch scenario=%s stop=%u formula=%" PRIu64
                        " measured=%" PRIu64 "\n",
                name, stop_index, predicted_stop_retire, measured_stop_retire);
        return 1;
    }
    const uint64_t stop_retire = measured_stop_retire;
    if (stop_retire < 64u) {
        fputs("partition-stop-window-too-early\n", stderr);
        return 1;
    }
    const uint64_t prefix_budget = stop_retire - 64u;
    partition_machine prefix;
    partition_snap snapshot = {0};
    if (partition_machine_create(scenario, &prefix) != 0) return 1;
    gbb_run_result prefix_result = {0};
    if (partition_run_budget(&prefix, prefix_budget, &local_meter,
                             GBB_STOP_HALTED_IDLE, &prefix_result) != 0 ||
        prefix_result.consumed_half_dots == 0u ||
        prefix_result.consumed_half_dots > prefix_budget ||
        prefix.machine->time_half_dots > stop_retire - 64u) {
        fprintf(stderr, "partition-stop-prefix-fail scenario=%s expected=%" PRIu64
                        " actual=%" PRIu64 "\n", name, prefix_budget,
                prefix_result.consumed_half_dots);
        partition_machine_destroy(&prefix);
        return 1;
    }
    if (partition_snapshot(&prefix, &snapshot) != 0) {
        fprintf(stderr, "partition-stop-snapshot-fail scenario=%s\n", name);
        partition_machine_destroy(&prefix);
        partition_snapshot_destroy(&snapshot);
        return 1;
    }
    const uint64_t snapshot_time = prefix.machine->time_half_dots;
    const uint64_t continuation_total = stop_retire + 72u - snapshot_time;
    gbb_run_result reference_result = {0};
    if (partition_run_budget(&prefix, continuation_total, &local_meter,
                             GBB_STOP_HALTED_IDLE, &reference_result) != 0) {
        fprintf(stderr, "partition-stop-reference-fail scenario=%s\n", name);
        partition_machine_destroy(&prefix);
        partition_snapshot_destroy(&snapshot);
        return 1;
    }
    const uint64_t reference = partition_digest(prefix.machine, &prefix.streams);
    for (int offset = -64; offset <= 64; ++offset) {
        const uint64_t absolute_cut = (uint64_t)((int64_t)stop_retire + offset);
        if (absolute_cut < snapshot_time) {
            partition_machine_destroy(&prefix);
            partition_snapshot_destroy(&snapshot);
            fputs("partition-stop-cut-before-snapshot\n", stderr);
            return 1;
        }
        if (partition_compare_snapshot_cut(scenario, &snapshot,
                absolute_cut - snapshot_time, continuation_total, reference,
                &local_meter, name) != 0) {
            partition_machine_destroy(&prefix);
            partition_snapshot_destroy(&snapshot);
            return 1;
        }
    }
    partition_machine_destroy(&prefix);
    partition_snapshot_destroy(&snapshot);
    if (local_meter.consumed_half_dots >
        GBB_PARTITION_CASE_HALF_DOT_CAP - meter->consumed_half_dots) {
        fputs("partition-cap-exceeded\n", stderr);
        return 1;
    }
    meter->consumed_half_dots += local_meter.consumed_half_dots;
    printf("%s stop=%u pass cuts=129 emulated_half_dots=%" PRIu64 "\n",
           name, stop_index, local_meter.consumed_half_dots);
    return 0;
}

static uint64_t rng_next(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    return *state = x;
}

static void sort_u64(uint64_t *values, size_t count) {
    for (size_t i = 1u; i < count; ++i) {
        const uint64_t value = values[i];
        size_t j = i;
        while (j != 0u && values[j - 1u] > value) {
            values[j] = values[j - 1u];
            --j;
        }
        values[j] = value;
    }
}

static int compare_cut_list(const partition_scenario *scenario,
                            const uint64_t *cuts, size_t count, uint64_t total,
                            const char *name, partition_meter *meter,
                            uint64_t *out_reference) {
    uint64_t reference = 0u;
    if (partition_run_reference(scenario, total, meter, &reference) != 0) return 1;
    uint64_t actual = 0u;
    if (partition_run_cut(scenario, cuts, count, total, meter, &actual) != 0) return 1;
    if (actual != reference) {
        fprintf(stderr, "partition-mismatch scenario=%s cuts=%zu reference=%016" PRIx64
                        " actual=%016" PRIx64 "\n", name, count, reference, actual);
        return 1;
    }
    if (out_reference != NULL) *out_reference = reference;
    return 0;
}

static int cgb_partition_interior_points(void) {
    partition_meter meter = {0};
    partition_scenario to_double = {0};
    const uint64_t double_stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
        GBB_HALF_DOTS_PER_T_DOUBLE;
    uint64_t double_cuts[24];
    size_t double_count = 0u;
    for (unsigned power = 2u; power <= 17u; ++power)
        double_cuts[double_count++] = UINT64_C(1) << power;
    const uint64_t double_m = half_dots_per_m(1u);
    for (unsigned bucket = 1u; bucket <= 4u; ++bucket) {
        uint64_t center = (double_stall * bucket / 5u) / double_m * double_m;
        double_cuts[double_count++] = center - 1u;
        double_cuts[double_count++] = center + 1u;
    }
    sort_u64(double_cuts, double_count);
    const uint64_t double_total = partition_stop_retire_half_dots(&to_double) +
        double_stall + partition_stall_tail(&to_double,
            partition_stop_retire_half_dots(&to_double)) + 64u;
    REQUIRE(double_count == 24u);
    REQUIRE(compare_cut_list(&to_double, double_cuts, double_count, double_total,
        "cgb_partition_interior_points_to_double", &meter, NULL) == 0);

    partition_scenario to_normal = {0};
    to_normal.start_double = 1u;
    const uint64_t normal_stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
        GBB_HALF_DOTS_PER_T_NORMAL;
    uint64_t normal_cuts[8];
    size_t normal_count = 0u;
    const uint64_t normal_m = half_dots_per_m(0u);
    for (unsigned bucket = 1u; bucket <= 4u; ++bucket) {
        uint64_t center = (normal_stall * bucket / 5u) / normal_m * normal_m;
        normal_cuts[normal_count++] = center - 1u;
        normal_cuts[normal_count++] = center + 1u;
    }
    sort_u64(normal_cuts, normal_count);
    const uint64_t normal_total = partition_stop_retire_half_dots(&to_normal) +
        normal_stall + partition_stall_tail(&to_normal,
            partition_stop_retire_half_dots(&to_normal)) + 64u;
    REQUIRE(normal_count == 8u);
    REQUIRE(compare_cut_list(&to_normal, normal_cuts, normal_count, normal_total,
        "cgb_partition_interior_points_to_normal", &meter, NULL) == 0);
    printf("cgb_partition_interior_points pass double=24 normal=8 emulated_half_dots=%" PRIu64 "\n",
           meter.consumed_half_dots);
    return 0;
}

static int cgb_partition_seeded_multicut(void) {
    partition_scenario scenario = {0};
    scenario.prepare_at_stall = 1u;
    scenario.seeded_stall_half_dots = 4096u;
    const uint64_t total = 4096u;
    uint64_t rng = UINT64_C(0x9E3779B97F4A7C15);
    partition_meter meter = {0};
    for (unsigned testcase = 0u; testcase < 256u; ++testcase) {
        const size_t count = 2u + (size_t)(rng_next(&rng) % 5u);
        uint64_t cuts[6];
        for (size_t i = 0u; i < count; ++i)
            cuts[i] = 1u + rng_next(&rng) % (total - 1u);
        for (size_t i = 1u; i < count; ++i) {
            const uint64_t value = cuts[i];
            size_t j = i;
            while (j != 0u && cuts[j - 1u] > value) {
                cuts[j] = cuts[j - 1u];
                --j;
            }
            cuts[j] = value;
        }
        uint64_t reference = 0u;
        if (partition_run_reference(&scenario, total, &meter, &reference) != 0) {
            fprintf(stderr, "partition-seed-fail seed=%016" PRIx64 " case=%u\n",
                    rng, testcase);
            return 1;
        }
        uint64_t actual = 0u;
        if (partition_run_cut(&scenario, cuts, count, total, &meter, &actual) != 0 ||
            actual != reference) {
            fprintf(stderr, "partition-seed-fail seed=%016" PRIx64 " case=%u\n",
                    rng, testcase);
            return 1;
        }
    }
    printf("cgb_partition_seeded_multicut pass cases=256 seed=9e3779b97f4a7c15 emulated_half_dots=%" PRIu64 "\n",
           meter.consumed_half_dots);
    return 0;
}

static int cgb_partition_zero_and_subquantum(void) {
    const uint64_t double_budgets[] = {0u, 1u, 3u};
    for (unsigned speed_case = 0u; speed_case < 2u; ++speed_case) {
        partition_scenario scenario = {0};
        if (speed_case != 0u) scenario.start_double = 1u;
        partition_meter meter = {0};
        partition_machine run;
        REQUIRE(partition_machine_create(&scenario, &run) == 0);
        REQUIRE(partition_prepare_stall(&run, &scenario, &meter) == 0);
        const uint64_t before = partition_digest(run.machine, &run.streams);
        const uint64_t *budgets = speed_case == 0u ? double_budgets : NULL;
        const size_t count = speed_case == 0u ? 3u : 1u;
        for (size_t i = 0u; i < count; ++i) {
            const uint64_t budget = speed_case == 0u ? budgets[i] : 7u;
            gbb_audio_frame frames[4];
            size_t frame_count = 0u;
            gbb_run_result result = gbb_run_audio(run.machine, budget, frames,
                sizeof(frames) / sizeof(frames[0]), &frame_count);
            REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
            REQUIRE(frame_count == 0u);
            REQUIRE(partition_digest(run.machine, &run.streams) == before);
        }
        if (speed_case == 0u) {
            gbb_audio_frame frames[4];
            size_t frame_count = 0u;
            gbb_run_result result = gbb_run_audio(run.machine, 4u, frames,
                sizeof(frames) / sizeof(frames[0]), &frame_count);
            REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 4u);
        }
        partition_machine_destroy(&run);
    }
    puts("cgb_partition_zero_and_subquantum pass budgets=0,1,3,4,7");
    return 0;
}

static int partition_delayed_ime_stop_time(uint64_t *stop_retire,
                                           partition_meter *meter) {
    partition_scenario scenario = {0};
    scenario.delayed_ime_timer_guest = 1u;
    partition_machine probe;
    if (partition_machine_create(&scenario, &probe) != 0) return 1;
    size_t stop_pc = 0u;
    for (size_t pc = 0x100u; pc + 1u < 0x180u; ++pc) {
        if (probe.machine->rom[pc] == 0x10u && probe.machine->rom[pc + 1u] == 0x04u) {
            stop_pc = pc;
            break;
        }
    }
    if (stop_pc == 0u) {
        partition_machine_destroy(&probe);
        return 1;
    }
    unsigned instructions = 0u;
    int found = 0;
    while (instructions++ < 64u) {
        if (probe.machine->pc == stop_pc) {
            if (probe.machine->ime != 0 || probe.machine->ime_delay == 0u ||
                (probe.machine->ie & probe.machine->interrupt_flags & 0x04u) == 0u ||
                probe.machine->double_speed != 0u || probe.machine->key1_armed == 0u) {
                fputs("partition-delayed-ime-stop-precondition-fail\n", stderr);
                partition_machine_destroy(&probe);
                return 1;
            }
            decoded instruction = decode(probe.machine);
            const uint8_t cost = instruction_cost(probe.machine, instruction);
            gbb_run_result result;
            if (partition_run_budget(&probe, cost, meter, GBB_STOP_HALTED_IDLE,
                                     &result) != 0 || result.consumed_half_dots != cost ||
                probe.machine->pc != stop_pc + 1u || probe.machine->ime == 0 ||
                probe.machine->ime_delay != 0u || probe.machine->double_speed == 0u ||
                probe.machine->key1_armed != 0u ||
                probe.machine->cpu_stall_kind != GBB_STALL_NONE ||
                (probe.machine->ie & probe.machine->interrupt_flags & 0x04u) == 0u) {
                fputs("partition-delayed-ime-stop-switch-fail\n", stderr);
                partition_machine_destroy(&probe);
                return 1;
            }
            *stop_retire = probe.machine->time_half_dots;
            found = 1;
            break;
        }
        decoded instruction = decode(probe.machine);
        if (!instruction.supported || instruction.ticks == 0u) {
            fputs("partition-delayed-ime-stop-decode-fail\n", stderr);
            partition_machine_destroy(&probe);
            return 1;
        }
        const uint8_t cost = instruction_cost(probe.machine, instruction);
        gbb_run_result result;
        if (partition_run_budget(&probe, cost, meter, GBB_STOP_HALTED_IDLE,
                                 &result) != 0 || result.consumed_half_dots != cost) {
            partition_machine_destroy(&probe);
            return 1;
        }
    }
    partition_machine_destroy(&probe);
    if (!found) fputs("partition-delayed-ime-stop-not-reached\n", stderr);
    return found ? 0 : 1;
}

static int partition_delayed_ime_stop_window(partition_meter *meter) {
    partition_scenario scenario = {0};
    scenario.delayed_ime_timer_guest = 1u;
    const uint64_t total = 2000u;
    uint64_t stop_retire = 0u;
    if (partition_delayed_ime_stop_time(&stop_retire, meter) != 0 ||
        stop_retire < 64u || stop_retire + 64u >= total) return 1;

    partition_machine reference_run;
    if (partition_machine_create(&scenario, &reference_run) != 0) return 1;
    gbb_run_result reference_result;
    if (partition_run_budget(&reference_run, total, meter, GBB_STOP_HALTED_IDLE,
                             &reference_result) != 0 ||
        reference_result.consumed_half_dots != total ||
        reference_run.machine->double_speed != 1u ||
        reference_run.machine->key1_armed != 0u ||
        reference_run.machine->cpu_stall_kind != GBB_STALL_NONE ||
        reference_run.machine->wram[0][0] != 1u ||
        reference_run.machine->wram[0][1] != 0x42u ||
        (reference_run.machine->interrupt_flags & 0x04u) != 0u) {
        fputs("partition-delayed-ime-stop-natural-irq-fail\n", stderr);
        partition_machine_destroy(&reference_run);
        return 1;
    }
    const uint64_t expected = partition_digest(reference_run.machine,
                                               &reference_run.streams);
    partition_machine_destroy(&reference_run);

    for (int offset = -64; offset <= 64; ++offset) {
        const uint64_t cut = (uint64_t)((int64_t)stop_retire + offset);
        uint64_t actual = 0u;
        if (partition_run_cut(&scenario, &cut, 1u, total, meter, &actual) != 0)
            return 1;
        if (actual != expected) {
            fprintf(stderr, "partition-mismatch scenario=cgb_partition_pending_at_stop_delayed_ime_timer_irq"
                            " cut=%" PRIu64 " reference=%016" PRIx64 " actual=%016" PRIx64 "\n",
                    cut, expected, actual);
            return 1;
        }
    }
    printf("cgb_partition_pending_at_stop_delayed_ime_timer_irq pass stop_retire=%" PRIu64
           " emulated_half_dots=%" PRIu64 "\n", stop_retire, meter->consumed_half_dots);
    return 0;
}

static int partition_verify_pre_enabled_stop_preemption(partition_meter *meter) {
    partition_scenario scenario = {0};
    scenario.pending_case = 1u;
    scenario.ime_pre_enabled_before_stop = 1u;
    partition_machine probe;
    if (partition_machine_create(&scenario, &probe) != 0) return 1;
    const size_t stop_pc = partition_stop_pc(&scenario, 0u);
    unsigned steps = 0u;
    while (steps++ < 64u && probe.machine->pc != stop_pc) {
        decoded instruction = decode(probe.machine);
        if (!instruction.supported || instruction.ticks == 0u) {
            partition_machine_destroy(&probe);
            return 1;
        }
        const uint8_t cost = instruction_cost(probe.machine, instruction);
        gbb_run_result result;
        if (partition_run_budget(&probe, cost, meter, GBB_STOP_HALTED_IDLE,
                                 &result) != 0 || result.consumed_half_dots != cost) {
            partition_machine_destroy(&probe);
            return 1;
        }
    }
    if (probe.machine->pc != stop_pc || probe.machine->ime == 0 ||
        probe.machine->ime_delay != 0u ||
        (probe.machine->ie & probe.machine->interrupt_flags & 0x04u) == 0u ||
        probe.machine->key1_armed == 0u) {
        fputs("partition-preenabled-stop-precondition-fail\n", stderr);
        partition_machine_destroy(&probe);
        return 1;
    }
    gbb_run_result dispatch;
    if (partition_run_budget(&probe, 40u, meter, GBB_STOP_HALTED_IDLE,
                             &dispatch) != 0 || dispatch.consumed_half_dots != 40u ||
        probe.machine->pc != 0x0050u || probe.machine->double_speed != 0u ||
        probe.machine->key1_armed == 0u || probe.machine->stop_switch_pending != 0u ||
        (probe.machine->interrupt_flags & 0x04u) != 0u) {
        fputs("partition-preenabled-stop-not-preempted\n", stderr);
        partition_machine_destroy(&probe);
        return 1;
    }
    partition_machine_destroy(&probe);
    puts("cgb_partition_pending_at_stop_pre_enabled_ime_preempts_stop pass vector=0050");
    return 0;
}

static int cgb_partition_pending_at_stop(void) {
    partition_meter meter = {0};
    partition_scenario ime1_selector = {0};
    ime1_selector.pending_case = 1u;
    ime1_selector.ime_on_at_stop = 1u;
    partition_machine selector;
    REQUIRE(partition_machine_create(&ime1_selector, &selector) == 0);
    selector.machine->ime = 1;
    selector.machine->key1_armed = 1u;
    /* Supplementary selector seam: when IME is already enabled and IRQ is
     * pending, a real run loop would service the IRQ before decoding STOP. */
    REQUIRE(stop_case(selector.machine) == 3);
    selector.machine->pc = (uint16_t)partition_stop_pc(&ime1_selector, 0u);
    execute(selector.machine, (uint8_t)GBB_STOP_SWITCH_COST_HALF_DOTS);
    REQUIRE(selector.machine->stop_switch_pending == 3u);
    REQUIRE(selector.machine->pc == partition_stop_pc(&ime1_selector, 0u) + 1u);
    selector.machine->ime = 0;
    partition_machine_destroy(&selector);

    partition_scenario case3_delayed_ime_seeded = ime1_selector;
    REQUIRE(partition_stop_window(&case3_delayed_ime_seeded, 0u,
        "cgb_partition_pending_at_stop_case3_delayed_ime_seeded", &meter) == 0);
    partition_scenario pre_enabled_ime = {0};
    pre_enabled_ime.pending_case = 1u;
    pre_enabled_ime.ime_pre_enabled_before_stop = 1u;
    REQUIRE(partition_verify_pre_enabled_stop_preemption(&meter) == 0);
    REQUIRE(partition_stop_window(&pre_enabled_ime, 0u,
        "cgb_partition_pending_at_stop_pre_enabled_ime_preempts_stop", &meter) == 0);
    partition_scenario case3_ime0 = {0};
    case3_ime0.pending_case = 1u;
    REQUIRE(partition_stop_window(&case3_ime0, 0u,
        "cgb_partition_pending_at_stop_case3_ime0", &meter) == 0);
    partition_scenario case2 = {0};
    case2.pending_case = 1u;
    case2.held_button = 1u;
    REQUIRE(partition_stop_window(&case2, 0u,
        "cgb_partition_pending_at_stop_case2", &meter) == 0);
    REQUIRE(partition_delayed_ime_stop_window(&meter) == 0);
    printf("cgb_partition_pending_at_stop pass emulated_half_dots=%" PRIu64 "\n",
           meter.consumed_half_dots);
    return 0;
}

static int cgb_partition_held_button(void) {
    partition_scenario scenario = {0};
    scenario.held_button = 1u;
    partition_meter meter = {0};
    REQUIRE(partition_stop_window(&scenario, 0u, "cgb_partition_held_button", &meter) == 0);
    return 0;
}

static int cgb_partition_lcd_off(void) {
    partition_scenario scenario = {0};
    scenario.lcd_off = 1u;
    partition_meter meter = {0};
    REQUIRE(partition_stop_window(&scenario, 0u, "cgb_partition_lcd_off", &meter) == 0);
    return 0;
}

static int cgb_partition_back_to_back(void) {
    partition_scenario scenario = {0};
    scenario.switch_count = 2u;
    partition_meter meter = {0};
    for (unsigned stop = 0u; stop < scenario.switch_count; ++stop)
        REQUIRE(partition_stop_window(&scenario, stop, "cgb_partition_back_to_back", &meter) == 0);
    return 0;
}

static int cgb_partition_chained(void) {
    partition_scenario scenario = {0};
    scenario.switch_count = 4u;
    partition_meter meter = {0};
    for (unsigned stop = 0u; stop < scenario.switch_count; ++stop)
        REQUIRE(partition_stop_window(&scenario, stop, "cgb_partition_chained", &meter) == 0);
    return 0;
}

static int cgb_partition_sensitivity_joypad_shift(void) {
    partition_scenario early = {0};
    const uint64_t stop_retire = partition_stop_retire_half_dots(&early);
    early.button_at_half_dots = stop_retire + 256u;
    partition_scenario late = early;
    late.button_at_half_dots += half_dots_per_m(1u);
    const uint64_t total = stop_retire +
        (uint64_t)GBB_SPEED_SWITCH_STALL_T * GBB_HALF_DOTS_PER_T_DOUBLE + 4096u;
    partition_meter meter = {0};
    uint64_t early_digest = 0u;
    uint64_t late_digest = 0u;
    REQUIRE(partition_run_reference(&early, total, &meter, &early_digest) == 0);
    REQUIRE(partition_run_reference(&late, total, &meter, &late_digest) == 0);
    if (early_digest == late_digest) {
        fputs("partition-joypad-shift-inert\n", stderr);
        return 1;
    }
    printf("cgb_partition_sensitivity_joypad_shift pass delta_half_dots=%" PRIu64
           " emulated_half_dots=%" PRIu64 "\n", half_dots_per_m(1u),
           meter.consumed_half_dots);
    return 0;
}

static int cgb_partition_sensitivity_digest_input(void) {
    partition_scenario scenario = {0};
    const uint64_t total = partition_stop_retire_half_dots(&scenario) +
        partition_stall_half_dots(&scenario) + 4096u;
    partition_meter meter = {0};
    partition_machine run;
    REQUIRE(partition_machine_create(&scenario, &run) == 0);
    gbb_run_result result;
    REQUIRE(partition_run_budget(&run, total, &meter, GBB_STOP_HALTED_IDLE,
                                 &result) == 0);
    const uint64_t baseline = partition_digest(run.machine, &run.streams);
    REQUIRE(run.streams.pcm_count != 0u);
    REQUIRE(run.streams.serial_count != 0u);
    static const char *const groups[] = {
        "cpu", "time-speed-stall", "divider", "timer", "serial-dma", "ppu",
        "apu", "rtc", "interrupt-bus", "wram", "rgb555", "pcm", "serial-output"
    };
    for (size_t i = 0u; i < sizeof(groups) / sizeof(groups[0]); ++i) {
        gbb_instance changed = *run.machine;
        partition_streams changed_streams = run.streams;
        switch (i) {
            case 0u: changed.a ^= 1u; break;
            case 1u: changed.time_half_dots ^= 1u; break;
            case 2u: changed.divider_counter ^= 1u; break;
            case 3u: changed.tima ^= 1u; break;
            case 4u: changed.serial_edge_remaining ^= 1u; break;
            case 5u: changed.ppu_half_phase ^= 1u; break;
            case 6u: changed.apu_sequencer_step ^= 1u; break;
            case 7u: changed.cart.rtc_s ^= 1u; break;
            case 8u: changed.interrupt_flags ^= 1u; break;
            case 9u: changed.wram[0][0] ^= 1u; break;
            case 10u: changed.rgb_working[0] ^= 1u; break;
            case 11u: changed_streams.pcm[0].left ^= 1; break;
            case 12u: changed_streams.serial_output[0] ^= 1u; break;
            default: return 1;
        }
        if (partition_digest(&changed, &changed_streams) == baseline) {
            fprintf(stderr, "partition-inert-input %s\n", groups[i]);
            partition_machine_destroy(&run);
            return 1;
        }
    }
    uint8_t *rom_copy = malloc(run.machine->rom_size);
    if (rom_copy == NULL) {
        partition_machine_destroy(&run);
        return 1;
    }
    memcpy(rom_copy, run.machine->rom, run.machine->rom_size);
    rom_copy[0x100u] ^= 1u;
    gbb_instance changed_rom = *run.machine;
    changed_rom.rom = rom_copy;
    const int rom_is_sensitive = partition_digest(&changed_rom, &run.streams) != baseline;
    free(rom_copy);
    if (!rom_is_sensitive) {
        fputs("partition-inert-input immutable-rom\n", stderr);
        partition_machine_destroy(&run);
        return 1;
    }
    if (run.machine->cartridge_ram == NULL || run.machine->cartridge_ram_size == 0u) {
        fputs("partition-digest-cartridge-ram-unavailable\n", stderr);
        partition_machine_destroy(&run);
        return 1;
    }
    uint8_t *ram_copy = malloc(run.machine->cartridge_ram_size);
    if (ram_copy == NULL) {
        partition_machine_destroy(&run);
        return 1;
    }
    memcpy(ram_copy, run.machine->cartridge_ram, run.machine->cartridge_ram_size);
    ram_copy[0] ^= 1u;
    gbb_instance changed_ram = *run.machine;
    changed_ram.cartridge_ram = ram_copy;
    const int ram_is_sensitive = partition_digest(&changed_ram, &run.streams) != baseline;
    free(ram_copy);
    if (!ram_is_sensitive) {
        fputs("partition-inert-input cartridge-ram\n", stderr);
        partition_machine_destroy(&run);
        return 1;
    }
    partition_machine_destroy(&run);
    printf("cgb_partition_sensitivity_digest_input pass groups=%zu\n",
           sizeof(groups) / sizeof(groups[0]) + 2u);
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
    if (strcmp(argv[1], "cgb_partition_snapshot_fidelity") == 0)
        return cgb_partition_snapshot_fidelity();
    if (strcmp(argv[1], "cgb_partition_stall_end_window_to_double") == 0)
        return cgb_partition_stall_end_window_to_double();
    if (strcmp(argv[1], "cgb_partition_stall_end_window_to_normal") == 0)
        return cgb_partition_stall_end_window_to_normal();
    if (strcmp(argv[1], "cgb_partition_stall_end_window_seeded") == 0)
        return cgb_partition_stall_end_window_seeded();
    if (strcmp(argv[1], "cgb_partition_interior_points") == 0)
        return cgb_partition_interior_points();
    if (strcmp(argv[1], "cgb_partition_seeded_multicut") == 0)
        return cgb_partition_seeded_multicut();
    if (strcmp(argv[1], "cgb_partition_zero_and_subquantum") == 0)
        return cgb_partition_zero_and_subquantum();
    if (strcmp(argv[1], "cgb_partition_pending_at_stop") == 0)
        return cgb_partition_pending_at_stop();
    if (strcmp(argv[1], "cgb_partition_sensitivity_joypad_shift") == 0)
        return cgb_partition_sensitivity_joypad_shift();
    if (strcmp(argv[1], "cgb_partition_sensitivity_digest_input") == 0)
        return cgb_partition_sensitivity_digest_input();
    if (strcmp(argv[1], "cgb_partition_held_button") == 0)
        return cgb_partition_held_button();
    if (strcmp(argv[1], "cgb_partition_lcd_off") == 0)
        return cgb_partition_lcd_off();
    if (strcmp(argv[1], "cgb_partition_back_to_back") == 0)
        return cgb_partition_back_to_back();
    if (strcmp(argv[1], "cgb_partition_chained") == 0)
        return cgb_partition_chained();
    return 2;
}
