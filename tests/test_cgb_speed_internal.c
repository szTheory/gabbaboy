/* White-box speed checks (Phase 12). The baseline identity case is intentionally
 * committed before the first Phase 12 core change. */
#ifdef GBB_P12_CORE_SOURCE
#include GBB_P12_CORE_SOURCE
#else
#include "../src/core/gabbaboy.c"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef GBB_P12_MUTANT_BUILD
#include <errno.h>
extern uint64_t gbb_p12_mutants;
#endif

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define FRAME_HALF_DOTS 140448u
#define FNV_OFFSET UINT64_C(0xCBF29CE484222325)
#define FNV_PRIME UINT64_C(0x100000001B3)

typedef struct { const char *path; uint64_t digest; } speed_pin;

/* Recorded at the pre-phase head fb45111 from the unmodified core. These are
 * regression identities, not hardware evidence. */
static const speed_pin SPEED_PINS[] = {
    {"cgb-colour/colour-attr.gb", UINT64_C(0x20c5f5bcd3de4db5)},
    {"cgb-colour/colour-compat.gb", UINT64_C(0xcfb2b0a18be42fb5)},
    {"cgb-colour/colour-cram.gb", UINT64_C(0x40aa92e3715d65b5)},
    {"cgb-colour/colour-hblank.gb", UINT64_C(0x7194fc1cb88beeb5)},
    {"cgb-colour/colour-lcdc0.gb", UINT64_C(0x16eb0caed53fcdb5)},
    {"cgb-colour/colour-lcdoff.gb", UINT64_C(0x5612e439ca9135b5)},
    {"cgb-banking/banking-cgb.gb", UINT64_C(0x9d5155c3b02fcb95)},
    {"<inline-timer-serial-dma>", UINT64_C(0xef296435e5cc0741)}
};

static void hash_bytes(uint64_t *hash, const void *data, size_t size) {
    const uint8_t *bytes = data;
    for (size_t i = 0; i < size; ++i) {
        *hash ^= bytes[i];
        *hash *= FNV_PRIME;
    }
}

static uint8_t *read_file(const char *path, size_t *size) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return NULL;
    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return NULL; }
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) { fclose(file); return NULL; }
    uint8_t *bytes = malloc((size_t)length);
    if (bytes == NULL || fread(bytes, 1, (size_t)length, file) != (size_t)length) {
        free(bytes); fclose(file); return NULL;
    }
    fclose(file);
    *size = (size_t)length;
    return bytes;
}

static int digest_frames(gbb_instance *machine, uint64_t *hash) {
    uint16_t pixels[GBB_FRAME_PIXELS];
    gbb_frame_info info;
    for (unsigned frame = 0; frame < 30u; ++frame) {
        gbb_audio_frame audio[1024];
        size_t count = 0;
        gbb_run_result result = gbb_run_audio(machine, FRAME_HALF_DOTS,
            audio, sizeof(audio) / sizeof(audio[0]), &count);
        REQUIRE(result.reason == GBB_STOP_BUDGET ||
                result.reason == GBB_STOP_HALTED_IDLE ||
                result.reason == GBB_STOP_OUTPUT_FULL);
        for (;;) {
            for (size_t i = 0; i < count; ++i) {
                const uint16_t left = (uint16_t)audio[i].left;
                const uint16_t right = (uint16_t)audio[i].right;
                const uint8_t pcm[4] = {(uint8_t)left, (uint8_t)(left >> 8),
                                        (uint8_t)right, (uint8_t)(right >> 8)};
                hash_bytes(hash, pcm, sizeof(pcm));
            }
            if (result.reason != GBB_STOP_OUTPUT_FULL) break;
            result = gbb_run_audio(machine, FRAME_HALF_DOTS - result.consumed_half_dots,
                audio, sizeof(audio) / sizeof(audio[0]), &count);
            REQUIRE(result.reason == GBB_STOP_BUDGET ||
                    result.reason == GBB_STOP_HALTED_IDLE ||
                    result.reason == GBB_STOP_OUTPUT_FULL);
        }
        if (gbb_copy_frame_rgb555(machine, pixels, sizeof(pixels),
                GBB_FRAME_WIDTH * sizeof(uint16_t), &info) == GBB_OK) {
            for (size_t p = 0; p < sizeof(pixels) / sizeof(pixels[0]); ++p) {
                const uint8_t rgb[2] = {(uint8_t)pixels[p], (uint8_t)(pixels[p] >> 8)};
                hash_bytes(hash, rgb, sizeof(rgb));
            }
        }
    }
    return 0;
}

static int pin_rom(const char *path, uint64_t *digest) {
    size_t rom_size = 0;
    uint8_t *rom = read_file(path, &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    *digest = FNV_OFFSET;
    int rc = digest_frames(machine, digest);
    gbb_destroy(machine);
    free(rom);
    return rc;
}

static int inline_guest(uint64_t *digest) {
    uint8_t rom[32768] = {0};
    rom[0x143] = 0xC0;
    rom[0x147] = 0;
    rom[0x148] = 0;
    rom[0x149] = 0;
    const uint8_t setup[] = {
        0x3E,0x05,0xE0,0x07, 0x3E,0xA5,0xE0,0x01, 0x3E,0x81,0xE0,0x02,
        0xC3,0x50,0x01
    };
    const uint8_t code[] = {
        0x3E,0xC0,0xE0,0x46, 0x21,0x00,0xC0, 0x06,0x40,
        0xF0,0x04,0x22, 0xF0,0x05,0x22, 0xF0,0x01,0x22, 0xF0,0x02,0x22,
        0xF0,0x0F,0x22, 0x05,0x20,0xEE, 0x18,0xFE
    };
    memcpy(rom + 0x100, setup, sizeof(setup));
    memset(rom + 0x150, 0x00, 4096u);
    memcpy(rom + 0x1150, code, sizeof(code));
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    machine->joypad_select = 0x30u;
    gbb_run_result run = gbb_run(machine, UINT64_C(200000), NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    gbb_trace_record snapshot;
    memset(&snapshot, 0, sizeof(snapshot));
    gbb_test_cpu_snapshot(machine, &snapshot);
    *digest = FNV_OFFSET;
    hash_bytes(digest, &snapshot, sizeof(snapshot));
    hash_bytes(digest, machine->wram[0], 320u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_identity_pin(const char *root, int flip) {
    char path[1024];
    int mismatch = 0;
    for (size_t i = 0; i < sizeof(SPEED_PINS) / sizeof(SPEED_PINS[0]) - 1u; ++i) {
        (void)snprintf(path, sizeof(path), "%s/%s", root, SPEED_PINS[i].path);
        uint64_t actual = 0;
        REQUIRE(pin_rom(path, &actual) == 0);
        const uint64_t expected = SPEED_PINS[i].digest ^ (flip ? UINT64_C(1) : UINT64_C(0));
        if (actual != expected) {
            fprintf(stderr, "observed %s %016llx\n", SPEED_PINS[i].path,
                    (unsigned long long)actual);
            mismatch = 1;
        }
    }
    uint64_t actual = 0;
    REQUIRE(inline_guest(&actual) == 0);
    const uint64_t expected = SPEED_PINS[7].digest ^ (flip ? UINT64_C(1) : UINT64_C(0));
    if (actual != expected) {
        fprintf(stderr, "observed %s %016llx\n", SPEED_PINS[7].path,
                (unsigned long long)actual);
        mismatch = 1;
    }
    return mismatch;
}

static int cgb_speed_internal_harness_alive(void) {
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    gbb_destroy(machine);
    return 0;
}

static int run_tracer_guest(int with_trace) {
    _Static_assert(sizeof(gbb_trace_record) == 24u,
                   "trace record has no speed field (D-13)");
    uint8_t rom[32768] = {0};
    rom[0x143] = 0xC0;
    rom[0x147] = 0u;
    rom[0x148] = 0u;
    rom[0x149] = 0u;
    const uint8_t code[] = {
        0x3E,0x01, 0xE0,0x4D, 0xF0,0x4D, 0xEA,0x00,0xC0,
        0x10,0x00, 0xF0,0x4D, 0xEA,0x01,0xC0, 0xF0,0x04,
        0xEA,0x02,0xC0, 0x76
    };
    memcpy(rom + 0x100, code, sizeof(code));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    machine->joypad_select = 0x30u;

    gbb_trace_record records[16];
    size_t traced = 0u;
    gbb_trace_record *trace = with_trace ? records : NULL;
    size_t capacity = with_trace ? 16u : 0u;
    const uint64_t want_to_double = GBB_SPEED_SWITCH_STALL_T * GBB_HALF_DOTS_PER_T_DOUBLE;
    gbb_run_result result = gbb_run(machine, 112u, trace, capacity);
    REQUIRE(!machine->stopped);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 112u);
    traced += result.trace_count;
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x7Fu);
    uint8_t speed = 0u, kind = 0u, armed = 0u;
    uint32_t remaining = 0u;
    gbb_test_speed_state(machine, &speed, &kind, &remaining, &armed);
    REQUIRE(speed == 1u && kind == GBB_STALL_SPEED_SWITCH && armed == 0u);
    REQUIRE(remaining == want_to_double && machine->divider_counter == 0u && !machine->stopped);

    result = gbb_run(machine, 1000u, trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 1000u);
    REQUIRE(result.trace_count == 0u);
    traced += result.trace_count;
    result = gbb_run(machine, 3u, trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
    REQUIRE(result.trace_count == 0u);
    traced += result.trace_count;
    result = gbb_run(machine, want_to_double - 1000u,
                     trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_BUDGET &&
            result.consumed_half_dots == want_to_double - 1000u);
    REQUIRE(result.trace_count == 0u);
    traced += result.trace_count;
    REQUIRE(machine->time_half_dots == 112u + want_to_double);
    REQUIRE(machine->divider_counter != 0u);
    gbb_test_speed_state(machine, &speed, &kind, &remaining, &armed);
    REQUIRE(speed == 1u && kind == GBB_STALL_NONE && remaining == 0u && armed == 0u);

    result = gbb_run(machine, 60u, trace == NULL ? NULL : records + traced,
                     trace == NULL ? 0u : 16u - traced);
    REQUIRE(result.reason == GBB_STOP_HALTED_IDLE && result.consumed_half_dots <= 60u);
    traced += result.trace_count;
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFEu);
    if (with_trace) {
        unsigned stops = 0u;
        for (size_t i = 0; i < traced; ++i)
            if (records[i].opcode_size != 0u && records[i].opcode[0] == 0x10u) ++stops;
        REQUIRE(traced == 10u && stops == 1u);
    }
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_tracer_switch(void) {
    REQUIRE(run_tracer_guest(0) == 0);
    REQUIRE(run_tracer_guest(1) == 0);
    return 0;
}

static int make_internal_rom(uint8_t rom[32768], const uint8_t *program, size_t program_size);
static int create_internal_machine(const uint8_t rom[32768], gbb_instance **out);
static int make_stop_test_machine(const uint8_t *program, size_t size, gbb_instance **out);

static void set_speed_pause_ppu_fixture(gbb_instance *machine) {
    machine->lcdc = 0x91u;
    machine->bgp = 0xE4u;
    machine->ly = 0u;
    machine->lyc = 0u;
    machine->ppu_mode = 2u;
    machine->ppu_dot = 0u;
    machine->ppu_half_phase = 0u;
    machine->stat = 0x86u;
    machine->scx = 0u;
    machine->scy = 0u;
    machine->wx = 0u;
    machine->wy = 0u;
    machine->frame_generation = 0u;
    memset(machine->vram, 0, sizeof(machine->vram));
    for (unsigned row = 0u; row < 8u; ++row) {
        machine->vram[0][row * 2u] = (row & 1u) ? 0xAAu : 0x55u;
        machine->vram[0][row * 2u + 1u] = (row & 1u) ? 0x33u : 0xCCu;
    }
    for (unsigned i = 0u; i < 4u; ++i) {
        const uint16_t color = (uint16_t[]){0x0000u, 0x001Fu, 0x03E0u, 0x7C00u}[i];
        machine->bg_cram[i * 2u] = (uint8_t)color;
        machine->bg_cram[i * 2u + 1u] = (uint8_t)(color >> 8);
    }
}

static int cgb_speed_xfail_pause_ppu_output(void) {
    const uint8_t switching_guest[] = {
        0x3Eu, 0x01u,             /* arm KEY1 */
        0xE0u, 0x4Du,
        0x10u, 0x00u              /* STOP; blank ROM bytes busy-wait after the pause */
    };
    const uint8_t busy_wait_guest[] = {0x00u, 0x18u, 0xFDu};
    uint8_t switching_rom[32768], busy_wait_rom[32768];
    make_internal_rom(switching_rom, switching_guest, sizeof(switching_guest));
    make_internal_rom(busy_wait_rom, busy_wait_guest, sizeof(busy_wait_guest));
    gbb_instance *switching = NULL, *busy_wait = NULL;
    REQUIRE(create_internal_machine(switching_rom, &switching) == 0);
    REQUIRE(create_internal_machine(busy_wait_rom, &busy_wait) == 0);
    set_speed_pause_ppu_fixture(switching);
    set_speed_pause_ppu_fixture(busy_wait);
    switching->joypad_select = busy_wait->joypad_select = 0x30u;

    gbb_run_result switched = {0};
    unsigned steps = 0u;
    while (switching->cpu_stall_kind == GBB_STALL_NONE && steps++ < 16u) {
        switched = gbb_run(switching, 256u, NULL, 0u);
        REQUIRE(switched.reason == GBB_STOP_BUDGET);
    }
    REQUIRE(switching->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    while (switching->cpu_stall_kind != GBB_STALL_NONE && steps++ < 1024u) {
        switched = gbb_run(switching, 256u, NULL, 0u);
        REQUIRE(switched.reason == GBB_STOP_BUDGET);
    }
    REQUIRE(switching->cpu_stall_kind == GBB_STALL_NONE);
    REQUIRE(switching->time_half_dots <= FRAME_HALF_DOTS &&
            (FRAME_HALF_DOTS - switching->time_half_dots) % 4u == 0u);
    switched = gbb_run(switching, FRAME_HALF_DOTS - switching->time_half_dots,
                       NULL, 0u);
    gbb_run_result waited = gbb_run(busy_wait, FRAME_HALF_DOTS, NULL, 0u);
    REQUIRE(switched.reason == GBB_STOP_BUDGET &&
            switching->time_half_dots == FRAME_HALF_DOTS);
    REQUIRE(waited.reason == GBB_STOP_BUDGET &&
            busy_wait->time_half_dots == FRAME_HALF_DOTS);
    REQUIRE(switching->double_speed == 1u &&
            switching->cpu_stall_kind == GBB_STALL_NONE);

    uint16_t switched_frame[GBB_FRAME_PIXELS];
    uint16_t waited_frame[GBB_FRAME_PIXELS];
    gbb_frame_info info;
    const gbb_error switched_copy = gbb_copy_frame_rgb555(switching, switched_frame,
        sizeof(switched_frame), GBB_FRAME_WIDTH * sizeof(uint16_t), &info);
    const gbb_error waited_copy = gbb_copy_frame_rgb555(busy_wait, waited_frame,
        sizeof(waited_frame), GBB_FRAME_WIDTH * sizeof(uint16_t), &info);
    if (switched_copy != GBB_OK || waited_copy != GBB_OK) {
        fprintf(stderr, "frame differs across the speed-switch pause: RGB555 output unavailable\n");
        gbb_destroy(switching);
        gbb_destroy(busy_wait);
        return 1;
    }
    if (memcmp(switched_frame, waited_frame, sizeof(switched_frame)) != 0) {
        fprintf(stderr, "frame differs across the speed-switch pause\n");
        gbb_destroy(switching);
        gbb_destroy(busy_wait);
        return 1;
    }
    gbb_destroy(switching);
    gbb_destroy(busy_wait);
    return 0;
}

/* The guest configures IE, IF, TIMA/TMA/TAC, waits for its own timer IRQ,
 * disables the timer, arms KEY1, and executes STOP. The following INC B is
 * the one-byte case-3 marker. EI retires at STOP, so the second variant must
 * enter the timer vector through the ordinary run loop before INC B. */
static int timer_pending_stop_guest(int enable_ime) {
    uint8_t code[] = {
        0x06,0x00,             /* LD B,0 */
        0x3E,0x04,0xEA,0xFF,0xFF, /* IE = timer */
        0x3E,0x00,0xE0,0x0F,   /* IF = 0 */
        0x3E,0xFF,0xE0,0x05,   /* TIMA = FF */
        0x3E,0x00,0xE0,0x06,   /* TMA = 0 */
        0x3E,0x05,0xE0,0x07,   /* TAC = on, 16 T */
        0xF0,0x0F,0xE6,0x04,0x28,0xFA, /* wait for IF.2 */
        0x3E,0x00,0xE0,0x07,   /* stop further timer requests */
        0x3E,0x01,0xE0,0x4D,   /* arm KEY1 */
        0x00,                 /* EI in the enabled variant */
        0x10,0x04,           /* STOP; INC B (not an operand) */
        0x78,0xEA,0x00,0xC0, /* store B */
        0x79,0xEA,0x01,0xC0, /* store C, written by handler */
        0x18,0xFE            /* stable loop */
    };
    size_t stop_offset = 0u;
    for (size_t i = 1u; i + 1u < sizeof(code); ++i)
        if (code[i] == 0x10u && code[i + 1u] == 0x04u) stop_offset = i;
    REQUIRE(stop_offset != 0u);
    if (enable_ime) code[stop_offset - 1u] = 0xFBu;
    uint8_t rom[32768];
    make_internal_rom(rom, code, sizeof(code));
    rom[0x50u] = 0x0Eu; rom[0x51u] = 0x42u; rom[0x52u] = 0xD9u;
    gbb_instance *m = NULL;
    REQUIRE(create_internal_machine(rom, &m) == 0);
    m->pc = 0x100u;
    gbb_run_result run = gbb_run(m, 2000u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(m->double_speed == 1u && m->key1_armed == 0u);
    REQUIRE(m->cpu_stall_kind == GBB_STALL_NONE && m->cpu_stall_half_dots == 0u);
    REQUIRE(m->wram[0][0] == 1u);
    REQUIRE(m->wram[0][1] == (enable_ime ? 0x42u : 0u));
    REQUIRE((m->interrupt_flags & 0x04u) == (enable_ime ? 0u : 0x04u));
    gbb_destroy(m);
    return 0;
}

static int cgb_speed_wake_ime_on(void) {
    const uint8_t program[] = {
        0x3Eu,0x04u,0xEAu,0xFFu,0xFFu, /* IE = timer */
        0xAFu,0xE0u,0x0Fu,             /* IF = 0 */
        0x3Eu,0x42u,0xE0u,0x06u,       /* TMA = reload value */
        0x3Eu,0x80u,0xE0u,0x05u,       /* TIMA overflows about 2,000 half-dots later */
        0x3Eu,0x05u,0xE0u,0x07u,       /* TAC = enabled, 16 T per increment */
        0x3Eu,0x01u,0xE0u,0x4Du,       /* arm KEY1 */
        0xFBu,0x00u,                   /* EI; one retire before STOP */
        0x10u,0x04u,                   /* STOP; operand is ignored */
        0x18u,0xFEu                    /* stable loop after RETI */
    };
    const uint8_t handler[] = {
        0x3Eu,0x5Au,                   /* LD A,$5A */
        0xEAu,0x00u,0xC0u,             /* marker in WRAM */
        0xD9u                          /* RETI */
    };
    uint8_t rom[32768];
    make_internal_rom(rom, program, sizeof(program));
    memcpy(rom + 0x50u, handler, sizeof(handler));
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x100u;
    machine->joypad_select = 0x30u;

    unsigned instructions = 0u;
    while (machine->cpu_stall_kind == GBB_STALL_NONE && instructions++ < 64u) {
        const uint8_t cost = instruction_cost(machine, decode(machine));
        gbb_run_result step = gbb_run(machine, cost, NULL, 0u);
        REQUIRE(step.reason == GBB_STOP_BUDGET && step.consumed_half_dots == cost);
    }
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    REQUIRE(machine->double_speed == 1u && machine->ime == 1);
    const uint64_t stall_start = machine->time_half_dots;

    gbb_trace_record record;
    gbb_run_result run = gbb_run(machine, 4096u, &record, 1u);
    REQUIRE(run.reason == GBB_STOP_TRACE_FULL && run.consumed_half_dots > 0u);
    REQUIRE(run.trace_count == 1u && record.pc == 0x0050u);
    REQUIRE(machine->timer_reloaded_at != UINT64_MAX);
    REQUIRE(machine->timer_reloaded_at > stall_start &&
            machine->timer_reloaded_at - stall_start >= 1800u &&
            machine->timer_reloaded_at - stall_start <= 2200u);
    const uint64_t stall_end = record.time_half_dots - (40u >> machine->double_speed);
    REQUIRE(stall_end >= machine->timer_reloaded_at &&
            stall_end - machine->timer_reloaded_at <= (8u >> machine->double_speed));
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE && machine->cpu_stall_half_dots == 0u);
    REQUIRE(machine->halt_bug == 0 && machine->double_speed == 1u);

    run = gbb_run(machine, 64u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && machine->wram[0][0] == 0x5Au);
    gbb_destroy(machine);
    return 0;
}

static int make_switch_test_machine(uint8_t speed, uint64_t time_half_dots,
                                    uint8_t ie, uint8_t interrupt_flags,
                                    int ime, gbb_instance **out) {
    const uint8_t program[] = {0x10u,0x00u,0x04u,0x00u};
    if (make_stop_test_machine(program, sizeof(program), out) != 0) return 1;
    (*out)->double_speed = speed;
    (*out)->time_half_dots = time_half_dots;
    (*out)->divider_counter = 0u;
    (*out)->divider_phase = 0u;
    (*out)->div = 0u;
    (*out)->key1_armed = 1u;
    (*out)->joypad_select = 0x30u;
    (*out)->ie = ie;
    (*out)->interrupt_flags = interrupt_flags;
    (*out)->ime = ime;
    return 0;
}

static int retire_internal_instruction(gbb_instance *machine) {
    decoded instruction = decode(machine);
    REQUIRE(instruction.supported && instruction.ticks != 0u);
    const uint8_t cost = instruction_cost(machine, instruction);
    gbb_run_result run = gbb_run(machine, cost, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == cost);
    return 0;
}

static int cgb_speed_wake_ime_off(void) {
    gbb_instance *machine = NULL;
    REQUIRE(make_switch_test_machine(0u, 0u, 0x04u, 0u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->double_speed == 1u &&
            machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    machine->tma = 0x27u;
    machine->timer_reload_pending = 1;
    machine->timer_reload_remaining = 2u;
    const uint64_t stall_start = machine->time_half_dots;

    gbb_run_result run = gbb_run(machine, 8u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 8u);
    REQUIRE(machine->timer_reloaded_at > stall_start &&
            machine->instruction_start_half_dots >= machine->timer_reloaded_at &&
            machine->instruction_start_half_dots - machine->timer_reloaded_at <= 4u);
    REQUIRE(machine->b == 1u && machine->ime == 0);
    REQUIRE((machine->interrupt_flags & 0x04u) != 0u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE &&
            machine->cpu_stall_half_dots == 0u && machine->halt_bug == 0);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_ei_stop(void) {
    const uint8_t program[] = {0xFBu,0x10u,0x00u,0x18u,0xFEu};
    const uint8_t handler[] = {0x3Eu,0x5Au,0xEAu,0x00u,0xC0u,0xD9u};
    uint8_t rom[32768];
    make_internal_rom(rom, program, sizeof(program));
    memcpy(rom + 0x50u, handler, sizeof(handler));
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x100u;
    machine->joypad_select = 0x30u;
    machine->key1_armed = 1u;
    machine->ie = 0x04u;
    machine->ime = 0;
    unsigned instructions = 0u;
    while (machine->cpu_stall_kind == GBB_STALL_NONE && instructions++ < 8u)
        REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    REQUIRE(machine->ime == 1);
    machine->tma = 0x42u;
    machine->timer_reload_pending = 1;
    machine->timer_reload_remaining = 2u;

    gbb_run_result run = gbb_run(machine, 64u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(machine->double_speed == 1u && machine->wram[0][0] == 0x5Au);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE &&
            machine->cpu_stall_half_dots == 0u && machine->halt_bug == 0);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_wake_m_boundary(void) {
    uint64_t reference_resume = UINT64_MAX;
    uint64_t reference_end = UINT64_MAX;
    for (uint32_t offset = 1u; offset <= 4u; ++offset) {
        for (unsigned split = 0u; split < 2u; ++split) {
            gbb_instance *machine = NULL;
            REQUIRE(make_switch_test_machine(0u, 0u, 0x04u, 0u, 0, &machine) == 0);
            REQUIRE(retire_internal_instruction(machine) == 0);
            REQUIRE(machine->double_speed == 1u &&
                    machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
            machine->tma = 0x31u;
            machine->timer_reload_pending = 1;
            machine->timer_reload_remaining = (uint8_t)offset;
            const uint64_t stall_start = machine->time_half_dots;

            gbb_run_result run = {0};
            if (split == 0u) {
                run = gbb_run(machine, 8u, NULL, 0u);
                REQUIRE(run.reason == GBB_STOP_BUDGET &&
                        run.consumed_half_dots == 8u);
            } else {
                const uint64_t budgets[] = {1u,3u,4u,7u};
                const uint64_t consumed[] = {0u,0u,4u,4u};
                for (size_t i = 0u; i < sizeof(budgets) / sizeof(budgets[0]); ++i) {
                    run = gbb_run(machine, budgets[i], NULL, 0u);
                    REQUIRE(run.reason == GBB_STOP_BUDGET &&
                            run.consumed_half_dots == consumed[i]);
                }
            }
            REQUIRE(machine->timer_reloaded_at == stall_start + offset);
            REQUIRE(machine->b == 1u && machine->ime == 0);
            REQUIRE(machine->instruction_start_half_dots >= machine->timer_reloaded_at &&
                    machine->instruction_start_half_dots - machine->timer_reloaded_at <= 4u);
            REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE &&
                    machine->cpu_stall_half_dots == 0u && machine->halt_bug == 0);
            if (split == 0u) {
                reference_resume = machine->instruction_start_half_dots;
                reference_end = machine->time_half_dots;
            } else {
                REQUIRE(machine->instruction_start_half_dots == reference_resume);
                REQUIRE(machine->time_half_dots == reference_end);
            }
            REQUIRE(machine->instruction_start_half_dots == stall_start + 4u);
            REQUIRE(machine->time_half_dots == stall_start + 8u);
            gbb_destroy(machine);
        }
    }
    return 0;
}

static int cgb_speed_realign(void) {
    gbb_instance *machine = NULL;
    REQUIRE(make_switch_test_machine(1u, 4u, 0x04u, 0x04u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->double_speed == 0u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SWITCH_REALIGN && machine->cpu_stall_half_dots == 4u);
    const uint64_t case3_tail_start = machine->time_half_dots;
    gbb_run_result run = gbb_run(machine, 3u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 0u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SWITCH_REALIGN && machine->cpu_stall_half_dots == 4u);
    run = gbb_run(machine, 4u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 4u);
    REQUIRE(machine->time_half_dots == case3_tail_start + 4u &&
            machine->cpu_stall_kind == GBB_STALL_NONE);
    gbb_destroy(machine);

    REQUIRE(make_switch_test_machine(1u, 0u, 0x04u, 0x04u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->double_speed == 0u &&
            machine->cpu_stall_kind == GBB_STALL_NONE &&
            machine->cpu_stall_half_dots == 0u);
    gbb_destroy(machine);

    REQUIRE(make_switch_test_machine(1u, 4u, 0u, 0u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->double_speed == 0u &&
            machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    const uint64_t normal_stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
                                  GBB_HALF_DOTS_PER_T_NORMAL;
    run = gbb_run(machine, normal_stall, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == normal_stall);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SWITCH_REALIGN && machine->cpu_stall_half_dots == 4u);
    const uint64_t completion_tail_start = machine->time_half_dots;
    run = gbb_run(machine, 4u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 4u);
    REQUIRE(machine->time_half_dots == completion_tail_start + 4u &&
            machine->cpu_stall_kind == GBB_STALL_NONE);
    gbb_destroy(machine);

    REQUIRE(make_switch_test_machine(1u, 4u, 0u, 0u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(gbb_run(machine, 8u, NULL, 0u).consumed_half_dots == 8u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
            (machine->time_half_dots & 7u) == 4u);
    machine->ie = 0x04u;
    machine->interrupt_flags = 0x04u;
    const uint64_t wake_tail_start = machine->time_half_dots;
    run = gbb_run(machine, 3u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 0u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SWITCH_REALIGN && machine->cpu_stall_half_dots == 4u);
    REQUIRE(machine->time_half_dots == wake_tail_start);
    run = gbb_run(machine, 4u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 4u);
    REQUIRE(machine->time_half_dots == wake_tail_start + 4u &&
            machine->cpu_stall_kind == GBB_STALL_NONE);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_stop_cases(void) {
    const uint8_t program[] = {0x10u, 0x3Eu, 0x42u, 0x00u};
    uint8_t rom[32768];
    make_internal_rom(rom, program, sizeof(program));
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x100u;
    machine->key1_armed = 1u;
    machine->ie = 4u;
    machine->interrupt_flags = 4u;
    machine->ime = 0u;
    machine->a = 0u;
    machine->f = 0xB0u;
    machine->divider_counter = 0x1234u;
    REQUIRE(stop_case(machine) == 3 && decode(machine).size == 1u);
    gbb_run_result result = gbb_run(machine, 16u, NULL, 0u);
    REQUIRE(machine->double_speed == 1u && machine->key1_armed == 0u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE && machine->cpu_stall_half_dots == 0u);
    REQUIRE(machine->pc == 0x101u && machine->a == 0u && machine->f == 0xB0u);
    REQUIRE(machine->divider_counter == 0u);
    gbb_destroy(machine);

    const uint8_t held_program[] = {0x10u, 0x3Cu, 0x00u};
    REQUIRE(make_stop_test_machine(held_program, sizeof(held_program), &machine) == 0);
    machine->key1_armed = 1u; machine->joypad_select = 0x20u;
    machine->ie = 0u; machine->interrupt_flags = 0u;
    machine->a = 0x81u; machine->f = 0x90u;
    machine->divider_counter = 0x1234u;
    const gbb_input_event press = {0u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_RIGHT};
    REQUIRE(gbb_queue_events(machine, &press, 1u) == GBB_OK);
    result = gbb_run(machine, 1u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
    decoded held_stop = decode(machine);
    REQUIRE(stop_case(machine) == 1 && held_stop.size == 2u);
    result = gbb_run(machine, 8u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_HALTED_IDLE && result.consumed_half_dots == 8u);
    REQUIRE(machine->pc == 0x102u);
    REQUIRE(machine->a == 0x81u && machine->f == 0x90u);
    REQUIRE(machine->halted);
    REQUIRE(!machine->double_speed && machine->key1_armed == 1u && machine->divider_counter == 0x1238u);
    machine->interrupt_flags = 1u;
    machine->ie = 1u;
    gbb_run(machine, 8u, NULL, 0u);
    REQUIRE(!machine->halted);
    gbb_destroy(machine);

    REQUIRE(make_stop_test_machine(held_program, sizeof(held_program), &machine) == 0);
    machine->key1_armed = 1u; machine->joypad_select = 0x20u;
    machine->ie = 1u; machine->interrupt_flags = 1u;
    machine->a = 0x81u; machine->f = 0x90u;
    REQUIRE(gbb_queue_events(machine, &press, 1u) == GBB_OK);
    result = gbb_run(machine, 1u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
    REQUIRE(stop_case(machine) == 2 && decode(machine).size == 1u);
    decoded held_pending = decode(machine);
    result = gbb_run(machine, 8u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 8u);
    REQUIRE(!machine->halted && !machine->double_speed && machine->key1_armed == 1u);
    REQUIRE(machine->pc == 0x101u);
    REQUIRE(machine->a == 0x81u && machine->f == 0x90u);
    gbb_destroy(machine);
    return 0;
}

static int make_stop_test_machine(const uint8_t *program, size_t size, gbb_instance **out) {
    uint8_t rom[32768];
    make_internal_rom(rom, program, size);
    if (create_internal_machine(rom, out) != 0) return 1;
    (*out)->pc = 0x100u;
    return 0;
}

typedef struct {
    gbb_trace_record cpu;
    uint64_t time_half_dots;
    uint32_t cpu_stall_half_dots;
    uint16_t divider_counter;
    uint8_t divider_phase, div, double_speed, cpu_stall_kind, stop_switch_pending;
    uint8_t key1_armed, ime, ime_delay, halted, stopped, halt_bug;
} cgb_speed_state_digest;

static void capture_cgb_speed_state(const gbb_instance *machine,
                                    cgb_speed_state_digest *digest) {
    memset(digest, 0, sizeof(*digest));
    gbb_test_cpu_snapshot(machine, &digest->cpu);
    digest->time_half_dots = machine->time_half_dots;
    digest->cpu_stall_half_dots = machine->cpu_stall_half_dots;
    digest->divider_counter = machine->divider_counter;
    digest->divider_phase = machine->divider_phase;
    digest->div = machine->div;
    digest->double_speed = machine->double_speed;
    digest->cpu_stall_kind = machine->cpu_stall_kind;
    digest->stop_switch_pending = machine->stop_switch_pending;
    digest->key1_armed = machine->key1_armed;
    digest->ime = (uint8_t)(machine->ime != 0);
    digest->ime_delay = machine->ime_delay;
    digest->halted = (uint8_t)(machine->halted != 0);
    digest->stopped = (uint8_t)(machine->stopped != 0);
    digest->halt_bug = (uint8_t)(machine->halt_bug != 0);
}

static int run_stall_length_case(uint8_t initial_speed, uint64_t initial_time,
                                 uint32_t half_dots_per_t) {
    gbb_instance *machine = NULL;
    REQUIRE(make_switch_test_machine(initial_speed, initial_time, 0u, 0u, 0,
                                     &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    const uint64_t stall_start = machine->time_half_dots;
    const uint64_t expected_stall = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
                                    (uint64_t)half_dots_per_t;
    const uint64_t m_cycle = (uint64_t)GBB_T_PER_M * (uint64_t)half_dots_per_t;
    REQUIRE(expected_stall % m_cycle == 0u);
    decoded next_instruction = decode(machine);
    const uint8_t next_cost = instruction_cost(machine, next_instruction);
    REQUIRE(next_cost != 0u);
    gbb_trace_record trace[1] = {{0}};
    gbb_run_result run = gbb_run(machine, expected_stall + next_cost, trace, 1u);
    REQUIRE(run.reason == GBB_STOP_BUDGET &&
            run.consumed_half_dots == expected_stall + next_cost &&
            run.trace_count == 1u);
    REQUIRE(trace[0].pc == 0x102u &&
            trace[0].time_half_dots == stall_start + expected_stall);
    REQUIRE(machine->b == 1u && machine->cpu_stall_kind == GBB_STALL_NONE &&
            machine->cpu_stall_half_dots == 0u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_stall_length(void) {
    REQUIRE(run_stall_length_case(0u, 0u, GBB_HALF_DOTS_PER_T_DOUBLE) == 0);
    REQUIRE(run_stall_length_case(1u, 0u, GBB_HALF_DOTS_PER_T_NORMAL) == 0);
    return 0;
}

static int check_stall_budget(gbb_instance *machine, uint64_t budget,
                              uint64_t expected_consumed) {
    const uint32_t remaining = machine->cpu_stall_half_dots;
    gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET &&
            run.consumed_half_dots == expected_consumed &&
            run.consumed_half_dots <= budget);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
            machine->cpu_stall_half_dots == remaining - (uint32_t)expected_consumed &&
            !machine->stopped && !machine->halted);
    return 0;
}

static int cgb_speed_budget_semantics(void) {
    gbb_instance *machine = NULL;
    REQUIRE(make_switch_test_machine(0u, 0u, 0u, 0u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(check_stall_budget(machine, 0u, 0u) == 0);
    REQUIRE(check_stall_budget(machine, 1u, 0u) == 0);
    REQUIRE(check_stall_budget(machine, 3u, 0u) == 0);
    REQUIRE(check_stall_budget(machine, 1001u, 1000u) == 0);
    gbb_destroy(machine);

    REQUIRE(make_switch_test_machine(1u, 4u, 0u, 0u, 0, &machine) == 0);
    REQUIRE(retire_internal_instruction(machine) == 0);
    for (uint64_t budget = 0u; budget < GBB_T_PER_M *
             GBB_HALF_DOTS_PER_T_NORMAL; ++budget)
        REQUIRE(check_stall_budget(machine, budget, 0u) == 0);
    REQUIRE(check_stall_budget(machine, 1001u, 1000u) == 0);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_never_stopped(void) {
    const uint8_t program[] = {
        0x10u,0x00u, 0x3Eu,0x01u, 0xE0u,0x4Du, 0x10u,0x00u, 0x76u
    };
    const uint64_t budgets[] = {1u,64u,4096u,140448u};
    gbb_instance *machine = NULL;
    REQUIRE(make_stop_test_machine(program, sizeof(program), &machine) == 0);
    machine->key1_armed = 1u;
    machine->joypad_select = 0x30u;
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    for (size_t call = 0u; call < 256u; ++call) {
        const int was_stalled = machine->cpu_stall_kind != GBB_STALL_NONE;
        const uint16_t divider_before = machine->divider_counter;
        const uint64_t budget = budgets[call % (sizeof(budgets) / sizeof(budgets[0]))];
        gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
        REQUIRE(run.reason != GBB_STOP_STOPPED && run.reason != GBB_STOP_NO_PROGRESS);
        if (was_stalled && run.consumed_half_dots != 0u)
            REQUIRE(machine->divider_counter != divider_before);
        if (run.reason == GBB_STOP_HALTED_IDLE) {
            REQUIRE(machine->halted && !machine->stopped && machine->double_speed == 0u &&
                    machine->cpu_stall_kind == GBB_STALL_NONE);
            REQUIRE(machine->pc == 0x109u);
            gbb_destroy(machine);
            return 0;
        }
        REQUIRE(run.reason == GBB_STOP_BUDGET && !machine->stopped && !machine->halted);
        if (machine->cpu_stall_kind != GBB_STALL_NONE)
            REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH ||
                    machine->cpu_stall_kind == GBB_STALL_SWITCH_REALIGN);
    }
    gbb_destroy(machine);
    REQUIRE(0 && "guest did not reach its terminal HALT within the bounded host-call loop");
    return 1;
}

static int cgb_speed_stall_devices_advance(void) {
    gbb_instance *machine = NULL;
    REQUIRE(make_switch_test_machine(0u, 0u, 0u, 0u, 0, &machine) == 0);
    for (size_t i = 0u; i < GBB_OAM_BYTES; ++i)
        machine->wram[0][i] = (uint8_t)(i + 1u);
    machine->dma_pending_page = 0xC0u;
    machine->dma_start_pending = 1;
    REQUIRE(retire_internal_instruction(machine) == 0);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH && machine->dma_active);

    machine->divider_counter = 0u;
    machine->divider_phase = 0u;
    machine->div = 0u;
    machine->tac = 0x04u;
    machine->tima = 0x20u;
    machine->tma = 0u;
    machine->timer_signal = timer_input(machine);
    machine->serial_active = 1;
    machine->serial_control = 1u;
    machine->serial_bits = 0u;
    machine->serial_edge_remaining = 512u;
    const uint8_t initial_tima = machine->tima;
    const uint8_t initial_ly = machine->ly;
    const uint16_t initial_divider = machine->divider_counter;
    const uint64_t stall_length = (uint64_t)GBB_SPEED_SWITCH_STALL_T *
                                  GBB_HALF_DOTS_PER_T_DOUBLE;
    gbb_audio_frame frames[2048];
    size_t frame_count = 0u;
    gbb_run_result run = gbb_run_audio(machine, stall_length, frames,
        sizeof(frames) / sizeof(frames[0]), &frame_count);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == stall_length);
    REQUIRE(machine->ly >= 143u && machine->ly != initial_ly);
    REQUIRE((uint16_t)(machine->divider_counter - initial_divider) ==
            (uint16_t)stall_length);
    REQUIRE(machine->tima != initial_tima);
    REQUIRE(!machine->serial_active && machine->serial_bits == 8u);
    REQUIRE(!machine->dma_active && machine->oam[0] == 1u &&
            machine->oam[GBB_OAM_BYTES - 1u] == (uint8_t)GBB_OAM_BYTES);
    REQUIRE(frame_count != 0u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_headroom(void) {
    gbb_instance *machine = NULL;
    REQUIRE(make_switch_test_machine(0u, 0u, 0u, 0u, 0, &machine) == 0);
    const uint8_t cost = instruction_cost(machine, decode(machine));
    const uint64_t required = (uint64_t)cost +
        2u * (uint64_t)GBB_SPEED_SWITCH_STALL_T + 4u;
    const uint64_t short_headroom_time = UINT64_MAX - required + 1u;
    machine->time_half_dots = short_headroom_time;
    cgb_speed_state_digest before, after;
    capture_cgb_speed_state(machine, &before);
    gbb_run_result run = gbb_run(machine, cost, NULL, 0u);
    capture_cgb_speed_state(machine, &after);
    REQUIRE(run.reason == GBB_STOP_INVALID_STATE && run.consumed_half_dots == 0u);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
    gbb_destroy(machine);

    REQUIRE(make_switch_test_machine(0u, 0u, 0u, 0u, 0, &machine) == 0);
    machine->time_half_dots = short_headroom_time - 1u;
    run = gbb_run(machine, cost, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == cost);
    REQUIRE(machine->double_speed == 1u &&
            machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
            machine->key1_armed == 0u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_stop_operand(void) {
    const uint8_t p0[] = {0x10u, 0x00u, 0x76u};
    const uint8_t p1[] = {0x10u, 0xFFu, 0x76u};
    gbb_instance *a = NULL, *b = NULL;
    REQUIRE(make_stop_test_machine(p0, sizeof(p0), &a) == 0);
    REQUIRE(make_stop_test_machine(p1, sizeof(p1), &b) == 0);
    a->key1_armed = b->key1_armed = 1u;
    a->joypad_select = b->joypad_select = 0x30u;
    gbb_run(a, 16u, NULL, 0u);
    gbb_run(b, 16u, NULL, 0u);
    gbb_trace_record snap_a, snap_b;
    memset(&snap_a, 0, sizeof(snap_a)); memset(&snap_b, 0, sizeof(snap_b));
    gbb_test_cpu_snapshot(a, &snap_a); gbb_test_cpu_snapshot(b, &snap_b);
    REQUIRE(memcmp(&snap_a, &snap_b, sizeof(snap_a)) == 0);
    REQUIRE(memcmp(a->wram, b->wram, sizeof(a->wram)) == 0);
    REQUIRE(a->key1_armed == b->key1_armed && a->time_half_dots == b->time_half_dots);
    gbb_destroy(a); gbb_destroy(b);
    return 0;
}

static int cgb_speed_stop_prefetch_ff04(int wrong_byte) {
    const uint8_t p[] = {0xC3u, 0x04u, 0xFFu};
    gbb_instance *m = NULL;
    REQUIRE(make_stop_test_machine(p, sizeof(p), &m) == 0);
    m->key1_armed = 1u;
    m->joypad_select = 0x30u;
    m->div = wrong_byte ? 0x11u : 0x10u;
    m->divider_counter = wrong_byte ? 0x1100u : 0x1000u;
    gbb_run_result run = gbb_run(m, 48u, NULL, 0u);
    REQUIRE(m->double_speed == 1u);
    REQUIRE(run.reason != GBB_STOP_UNSUPPORTED_BUS);
    gbb_destroy(m);
    return 0;
}

static int cgb_speed_stop_cost(void) {
    uint8_t rom[32768];
    const uint8_t p[] = {0x10u, 0x00u};
    make_internal_rom(rom, p, sizeof(p));
    gbb_instance *m = NULL;
    REQUIRE(create_internal_machine(rom, &m) == 0);
    m->pc = 0x100u; m->key1_armed = 1u; m->joypad_select = 0x30u;
    REQUIRE(decode(m).ticks == GBB_STOP_SWITCH_COST_HALF_DOTS);
    m->double_speed = 1u;
    REQUIRE(instruction_cost(m, decode(m)) == 8u);
    m->double_speed = 0u; m->ie = 4u; m->interrupt_flags = 4u;
    REQUIRE(decode(m).ticks == GBB_STOP_SWITCH_COST_HALF_DOTS);
    m->key1_armed = 0u;
    REQUIRE(decode(m).ticks == 8u);
    gbb_destroy(m);
    return 0;
}

static int cgb_speed_dmg_unarmed_unchanged(void) {
    const uint8_t p[] = {0x10u, 0x00u};
    uint8_t rom[32768]; make_internal_rom(rom, p, sizeof(p));
    gbb_instance *m = NULL;
    REQUIRE(create_internal_machine(rom, &m) == 0);
    m->pc = 0x100u; m->joypad_select = 0x30u;
    m->divider_counter = 0u;
    const uint8_t apu_before = m->apu_sequencer_step;
    gbb_run_result run = gbb_run(m, 16u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_STOPPED && m->double_speed == 0u);
    REQUIRE(m->divider_counter == 0u && m->apu_sequencer_step == apu_before);
    gbb_destroy(m);

    REQUIRE(create_internal_machine(rom, &m) == 0);
    m->pc = 0x100u; m->exec_mode = GBB_MODE_CGB_DMG_COMPAT; m->key1_armed = 1u;
    m->joypad_select = 0x30u; m->divider_counter = 0x1000u;
    m->apu_sequencer_step = 3u;
    run = gbb_run(m, 16u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_STOPPED && !m->double_speed);
    REQUIRE(m->apu_sequencer_step == 3u);
    gbb_destroy(m);
    return 0;
}

static int cgb_speed_key1_readback(void) {
    const uint8_t p[] = {0x10u, 0x00u};
    uint8_t rom[32768]; make_internal_rom(rom, p, sizeof(p));
    gbb_instance *m = NULL;
    REQUIRE(create_internal_machine(rom, &m) == 0);
    m->joypad_select = 0x30u;
    REQUIRE(bus_read(m, 0xFF4Du, 0u) == 0x7Eu);
    bus_write(m, 0xFF4Du, 1u, 0u);
    REQUIRE(bus_read(m, 0xFF4Du, 0u) == 0x7Fu);
    m->pc = 0x100u;
    gbb_run_result run = gbb_run(m, 32u, NULL, 0u);
    REQUIRE(run.reason != GBB_STOP_UNSUPPORTED_BUS && m->double_speed == 1u);
    REQUIRE(bus_read(m, 0xFF4Du, m->time_half_dots) == 0xFEu);
    bus_write(m, 0xFF4Du, 1u, m->time_half_dots);
    REQUIRE(bus_read(m, 0xFF4Du, m->time_half_dots) == 0xFFu);
    m->cpu_stall_half_dots = 0u; m->cpu_stall_kind = GBB_STALL_NONE;
    m->rom[0x102u] = 0x10u; m->rom[0x103u] = 0x00u; m->pc = 0x102u;
    run = gbb_run(m, 8u, NULL, 0u);
    REQUIRE(run.reason != GBB_STOP_UNSUPPORTED_BUS && m->double_speed == 0u);
    REQUIRE(bus_read(m, 0xFF4Du, m->time_half_dots) == 0x7Eu);
    gbb_destroy(m);
    return 0;
}

static int cgb_speed_key0_no_switch(void) {
    const uint8_t p[] = {0x10u, 0x00u};
    uint8_t rom[32768]; make_internal_rom(rom, p, sizeof(p));
    gbb_instance *m = NULL;
    REQUIRE(create_internal_machine(rom, &m) == 0);
    for (unsigned value = 0; value < 256u; ++value) {
        bus_write(m, 0xFF4Cu, (uint8_t)value, m->time_half_dots);
        REQUIRE(m->double_speed == 0u && m->exec_mode == GBB_MODE_CGB);
    }
    m->key1_armed = 1u;
    for (unsigned value = 0; value < 256u; ++value) {
        bus_write(m, 0xFF4Cu, (uint8_t)value, m->time_half_dots);
        REQUIRE(m->double_speed == 0u && m->exec_mode == GBB_MODE_CGB);
    }
    m->pc = 0x100u;
    gbb_run_result run = gbb_run(m, 32u, NULL, 0u);
    REQUIRE(run.reason != GBB_STOP_UNSUPPORTED_BUS && m->double_speed == 1u);
    gbb_destroy(m);
    return 0;
}

static int make_internal_rom(uint8_t rom[32768], const uint8_t *program, size_t program_size) {
    memset(rom, 0, 32768u);
    rom[0x143] = 0xC0u;
    rom[0x147] = 0u;
    rom[0x148] = 0u;
    rom[0x149] = 0u;
    if (program != NULL) memcpy(rom + 0x100u, program, program_size);
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    return 0;
}

static int create_internal_machine(const uint8_t rom[32768], gbb_instance **out) {
    *out = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, out) == GBB_OK);
    if (gbb_load_rom(*out, rom, 32768u) != GBB_OK) {
        gbb_destroy(*out);
        *out = NULL;
        return 1;
    }
    return 0;
}

static int cgb_speed_cpu_ticks(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x100u;
    for (unsigned op = 0u; op < 256u; ++op) {
        machine->rom[0x100u] = (uint8_t)op;
        machine->rom[0x101u] = 0xC0u;
        decoded d = decode(machine);
        REQUIRE(d.ticks % 8u == 0u);
        machine->double_speed = 0u;
        REQUIRE(instruction_cost(machine, d) == d.ticks);
        machine->double_speed = 1u;
        REQUIRE(instruction_cost(machine, d) == (uint8_t)(d.ticks / 2u));
    }
    machine->rom[0x100u] = 0xCBu;
    for (unsigned op = 0u; op < 256u; ++op) {
        machine->rom[0x101u] = (uint8_t)op;
        decoded d = decode(machine);
        REQUIRE(d.ticks % 8u == 0u);
        machine->double_speed = 0u;
        REQUIRE(instruction_cost(machine, d) == d.ticks);
        machine->double_speed = 1u;
        REQUIRE(instruction_cost(machine, d) == (uint8_t)(d.ticks / 2u));
    }

    const uint64_t offsets[] = {8u, 16u, 24u, 32u, 40u};
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        machine->double_speed = (uint8_t)speed;
        for (size_t i = 0u; i < sizeof(offsets) / sizeof(offsets[0]); ++i) {
            const uint64_t offset = offsets[i];
            REQUIRE(offset % 8u == 0u);
            uint64_t start = machine->time_half_dots;
            machine->instruction_start_half_dots = start;
            (void)bus_read(machine, 0xFF80u, offset);
            REQUIRE(machine->time_half_dots - start == (offset >> speed));
            start = machine->time_half_dots;
            machine->instruction_start_half_dots = start;
            bus_write(machine, 0xFF80u, 0u, offset);
            REQUIRE(machine->time_half_dots - start == (offset >> speed));
        }
    }
    gbb_destroy(machine);

    make_internal_rom(rom, NULL, 0u);
    memset(rom + 0x200u, 0u, 1000u);
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x200u;
    gbb_run_result run;
    for (unsigned i = 0u; i < 1000u; ++i) {
        run = gbb_run(machine, 8u, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 8u);
    }
    REQUIRE(machine->pc == 0x200u + 1000u);
    gbb_destroy(machine);

    const uint8_t switch_program[] = {0x3Eu, 0x01u, 0xE0u, 0x4Du, 0x10u, 0x00u};
    make_internal_rom(rom, switch_program, sizeof(switch_program));
    memset(rom + 0x300u, 0u, 1000u);
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    run = gbb_run(machine, 1024u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    uint8_t speed = 0u, kind = 0u, armed = 0u;
    uint32_t remaining = 0u;
    gbb_test_speed_state(machine, &speed, &kind, &remaining, &armed);
    REQUIRE(speed == 1u && kind == GBB_STALL_SPEED_SWITCH && armed == 0u && remaining > 0u);
    while (remaining != 0u) {
        run = gbb_run(machine, remaining, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots > 0u);
        gbb_test_speed_state(machine, &speed, &kind, &remaining, &armed);
    }
    machine->pc = 0x300u;
    for (unsigned i = 0u; i < 1000u; ++i) {
        run = gbb_run(machine, 4u, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 4u);
    }
    REQUIRE(machine->pc == 0x300u + 1000u);
    gbb_destroy(machine);

    for (unsigned speed_mode = 0u; speed_mode <= 1u; ++speed_mode) {
        make_internal_rom(rom, NULL, 0u);
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed_mode;
        machine->ime = 1u;
        machine->ie = 1u;
        machine->interrupt_flags = 1u;
        const uint64_t expected = speed_mode ? 20u : 40u;
        run = gbb_run(machine, expected, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == expected);
        REQUIRE(machine->pc == 0x40u);
        gbb_destroy(machine);
    }
    return 0;
}

static int cgb_speed_timer_scaling(void) {
    uint8_t rom[32768];
    const uint8_t timer_guest[] = {
        0x3Eu,0x05u,0xE0u,0x07u,0xF0u,0x44u,0x47u,
        0xF0u,0x05u,0xEAu,0x01u,0xC0u,0xF0u,0x04u,0xEAu,0x02u,0xC0u,
        0xF0u,0x44u,0xB8u,0x28u,0xFBu,0x47u,
        0xF0u,0x44u,0xB8u,0x28u,0xFBu,0x47u,
        0xF0u,0x05u,0xEAu,0x03u,0xC0u,0xF0u,0x04u,0xEAu,0x04u,0xC0u,
        0x3Eu,0xAAu,0xEAu,0x00u,0xC0u,0x18u,0xFEu
    };
    make_internal_rom(rom, timer_guest, sizeof(timer_guest));
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        machine->pc = 0x100u;
        for (unsigned calls = 0u; machine->wram[0][0] != 0xAAu && calls < 200u; ++calls) {
            const gbb_run_result run = gbb_run(machine, 64u, NULL, 0u);
            REQUIRE(run.reason == GBB_STOP_BUDGET);
        }
        REQUIRE(machine->wram[0][0] == 0xAAu);
        const unsigned tima_delta = (uint8_t)(machine->wram[0][3] - machine->wram[0][1]);
        const unsigned div_delta = (uint8_t)(machine->wram[0][4] - machine->wram[0][2]);
        if (speed == 0u) {
            REQUIRE(tima_delta >= 56u && tima_delta <= 58u);
            REQUIRE(div_delta >= 3u && div_delta <= 4u);
        } else {
            REQUIRE(tima_delta >= 113u && tima_delta <= 115u);
            REQUIRE(div_delta >= 7u && div_delta <= 8u);
        }
        gbb_destroy(machine);
    }

    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->tima = 0xFFu;
    timer_increment(machine, 0u);
    REQUIRE(machine->timer_reload_pending && machine->timer_reload_remaining == 4u);
    advance_devices_to(machine, 4u);
    REQUIRE(machine->timer_reload_pending && machine->timer_reload_remaining == 2u);
    machine->double_speed = 1u;
    advance_devices_to(machine, 6u);
    REQUIRE(!machine->timer_reload_pending && machine->timer_reload_remaining == 0u);
    REQUIRE(machine->tima == machine->tma);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_serial_scaling(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        machine->serial_active = 1;
        machine->serial_control = 1u;
        machine->serial_edge_remaining = 512u;
        const uint64_t duration = speed ? 4096u : 8192u;
        const uint64_t probe = duration - (speed ? 1u : 2u);
        advance_devices_to(machine, probe);
        REQUIRE(machine->serial_active);
        advance_devices_to(machine, duration);
        REQUIRE(!machine->serial_active);
        REQUIRE((machine->interrupt_flags & 0x08u) != 0u);
        gbb_destroy(machine);
    }
    return 0;
}

static int cgb_speed_dma_scaling(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        machine->dma_active = 1;
        machine->dma_page = 0xC0u;
        machine->dma_index = 0u;
        machine->dma_phase = 0u;
        const uint64_t half_dots_per_m = 8u >> speed;
        advance_devices_to(machine, 159u * half_dots_per_m);
        REQUIRE(machine->dma_active && machine->dma_index < GBB_OAM_BYTES);
        advance_devices_to(machine, 161u * half_dots_per_m);
        REQUIRE(!machine->dma_active && machine->dma_index == GBB_OAM_BYTES);
        gbb_destroy(machine);
    }
    return 0;
}

static int cgb_speed_apu_tap(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        machine->apu_power = 1u;
        machine->apu_pulse[0].control = 0x40u;
        machine->apu_pulse[0].length = 256u;
        machine->apu_pulse[0].envelope = 0x0Fu;
        machine->apu_pulse[0].envelope_timer = 7u;
        machine->apu_pulse[0].volume = 0u;
        advance_devices_to(machine, GBB_MASTER_HALF_DOTS_PER_SECOND);
        REQUIRE(machine->apu_pulse[0].volume == 9u);
        gbb_destroy(machine);
    }

    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->double_speed = 1u;
    machine->apu_power = 1u;
    machine->divider_counter = 0x2000u;
    machine->apu_sequencer_step = 3u;
    divider_reset(machine, 1);
    REQUIRE(machine->apu_sequencer_step == 4u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_remainder_across_switch(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x200u;
    machine->rom[0x200u] = 0x10u;
    machine->rom[0x201u] = 0x00u;
    machine->key1_armed = 1u;
    machine->dma_active = 1;
    machine->dma_page = 0xC0u;
    machine->dma_phase = 1u;
    machine->serial_active = 1;
    machine->serial_control = 1u;
    machine->serial_edge_remaining = 512u;
    machine->timer_reload_pending = 1;
    machine->timer_reload_remaining = 100u;
    gbb_run_result run = gbb_run(machine, 16u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(machine->double_speed == 1u && machine->cpu_stall_kind == GBB_STALL_SPEED_SWITCH);
    REQUIRE(machine->divider_phase < 2u);
    REQUIRE(machine->serial_edge_remaining > 0u && machine->serial_edge_remaining < 512u);
    REQUIRE(machine->dma_phase > 0u && machine->dma_phase < GBB_T_PER_M);
    REQUIRE(machine->timer_reload_remaining == 92u);
    gbb_destroy(machine);

    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->tima = 0xFFu;
    timer_increment(machine, 0u);
    REQUIRE(machine->timer_reload_remaining == 4u);
    gbb_destroy(machine);
    return 0;
}

static void set_header_checksum(uint8_t rom[32768]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int cgb_speed_ppu_apu_rtc_unscaled(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        machine->ly = 0u;
        machine->ppu_dot = 0u;
        machine->ppu_half_phase = 0u;
        const uint64_t frame_start = machine->frame_generation;
        advance_devices_to(machine, 912u);
        REQUIRE(machine->ly == 1u);
        advance_devices_to(machine, 140448u);
        REQUIRE(machine->frame_generation == frame_start + 1u);
        gbb_destroy(machine);

        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        machine->apu_pulse[0].enabled = 1;
        machine->apu_pulse[0].timer = 100u;
        advance_devices_to(machine, 10u);
        REQUIRE(machine->apu_pulse[0].timer == 90u);
        gbb_destroy(machine);
    }

    size_t pcm_counts[2] = {0u, 0u};
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        gbb_audio_frame pcm[1024];
        machine->audio_frames = pcm;
        machine->audio_frame_capacity = sizeof(pcm) / sizeof(pcm[0]);
        machine->audio_frame_count = 0u;
        advance_devices_to(machine, 140448u);
        pcm_counts[speed] = machine->audio_frame_count;
        gbb_destroy(machine);
    }
    REQUIRE(pcm_counts[0] > 0u && pcm_counts[0] == pcm_counts[1]);

    make_internal_rom(rom, NULL, 0u);
    rom[0x147u] = 0x10u;
    rom[0x149u] = 0x03u;
    set_header_checksum(rom);
    for (unsigned speed = 0u; speed <= 1u; ++speed) {
        gbb_instance *machine = NULL;
        REQUIRE(create_internal_machine(rom, &machine) == 0);
        machine->double_speed = (uint8_t)speed;
        rtc_sync(&machine->cart, 3u * GBB_MASTER_HALF_DOTS_PER_SECOND);
        rtc_latch_write(&machine->cart, 3u * GBB_MASTER_HALF_DOTS_PER_SECOND, 0u);
        rtc_latch_write(&machine->cart, 3u * GBB_MASTER_HALF_DOTS_PER_SECOND, 1u);
        REQUIRE(machine->cart.rtc_l[0] == 3u);
        gbb_destroy(machine);
    }
    return 0;
}

static int cgb_speed_reset_double_speed(void) {
    uint8_t rom[32768];
    const uint8_t switch_program[] = {0x3Eu, 0x01u, 0xE0u, 0x4Du, 0x10u, 0x00u};
    make_internal_rom(rom, switch_program, sizeof(switch_program));
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    gbb_run_result run = gbb_run(machine, 1024u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(machine->double_speed == 1u);
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(machine->double_speed == 0u);
    REQUIRE(bus_read(machine, 0xFF4Du, 0u) == 0x7Eu);
    memset(machine->rom + 0x200u, 0u, 1000u);
    machine->pc = 0x200u;
    const uint64_t start = machine->time_half_dots;
    for (unsigned i = 0u; i < 1000u; ++i) {
        run = gbb_run(machine, 8u, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 8u);
    }
    REQUIRE(machine->time_half_dots - start == 8000u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_reset_stall(void) {
    uint8_t rom[32768];
    make_internal_rom(rom, NULL, 0u);
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->cpu_stall_kind = GBB_STALL_SPEED_SWITCH;
    machine->cpu_stall_half_dots = 2048u;
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE);
    REQUIRE(machine->cpu_stall_half_dots == 0u);
    machine->pc = 0x200u;
    gbb_run_result run = gbb_run(machine, 8u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 8u);
    REQUIRE(machine->pc == 0x201u);
    gbb_destroy(machine);
    return 0;
}

static int cgb_speed_reset_key1(void) {
    uint8_t rom[32768];
    const uint8_t stop_program[] = {0x10u, 0x00u};
    make_internal_rom(rom, stop_program, sizeof(stop_program));
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->key1_armed = 1u;
    machine->time_half_dots = 32u;
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(machine->key1_armed == 0u);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(machine->key1_armed == 0u);
    machine->rom[0x200u] = 0x10u;
    machine->rom[0x201u] = 0x00u;
    machine->pc = 0x200u;
    gbb_run_result run = gbb_run(machine, 16u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_STOPPED);
    REQUIRE(machine->stopped == 1u && machine->double_speed == 0u);
    gbb_destroy(machine);
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
    if (strcmp(argv[1], "cgb_speed_internal_harness_alive") == 0) {
        int rc = cgb_speed_internal_harness_alive();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_internal_harness_alive pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_identity_pin") == 0) {
        if (argc < 3 || argc > 4) return 2;
        const int flip = argc == 4 && strcmp(argv[3], "--flip") == 0;
        if (argc == 4 && !flip) return 2;
        int rc = cgb_speed_identity_pin(argv[2], flip);
        if (rc == 0) puts("cgb-speed-internal cgb_speed_identity_pin pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_tracer_switch") == 0) {
        int rc = cgb_speed_tracer_switch();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_tracer_switch pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_xfail_pause_ppu_output") == 0) {
        int rc = cgb_speed_xfail_pause_ppu_output();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_xfail_pause_ppu_output pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_stop_cases") == 0) {
        int rc = cgb_speed_stop_cases();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_stop_cases pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_stop_guest_timer_irq") == 0) {
        REQUIRE(timer_pending_stop_guest(0) == 0);
        REQUIRE(timer_pending_stop_guest(1) == 0);
        puts("cgb-speed-internal cgb_speed_stop_guest_timer_irq pass");
        return 0;
    }
    if (strcmp(argv[1], "cgb_speed_wake_ime_on") == 0) {
        int rc = cgb_speed_wake_ime_on();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_wake_ime_on pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_wake_ime_off") == 0) return cgb_speed_wake_ime_off();
    if (strcmp(argv[1], "cgb_speed_ei_stop") == 0) return cgb_speed_ei_stop();
    if (strcmp(argv[1], "cgb_speed_wake_m_boundary") == 0) return cgb_speed_wake_m_boundary();
    if (strcmp(argv[1], "cgb_speed_realign") == 0) return cgb_speed_realign();
    if (strcmp(argv[1], "cgb_speed_stall_length") == 0) return cgb_speed_stall_length();
    if (strcmp(argv[1], "cgb_speed_budget_semantics") == 0) return cgb_speed_budget_semantics();
    if (strcmp(argv[1], "cgb_speed_never_stopped") == 0) return cgb_speed_never_stopped();
    if (strcmp(argv[1], "cgb_speed_stall_devices_advance") == 0) return cgb_speed_stall_devices_advance();
    if (strcmp(argv[1], "cgb_speed_headroom") == 0) return cgb_speed_headroom();
    if (strcmp(argv[1], "cgb_speed_stop_operand") == 0) return cgb_speed_stop_operand();
    if (strcmp(argv[1], "cgb_speed_stop_prefetch_ff04") == 0) {
        return cgb_speed_stop_prefetch_ff04(argc > 2 && strcmp(argv[2], "--ff04-wrong-byte") == 0);
    }
    if (strcmp(argv[1], "cgb_speed_stop_cost") == 0) return cgb_speed_stop_cost();
    if (strcmp(argv[1], "cgb_speed_dmg_unarmed_unchanged") == 0) return cgb_speed_dmg_unarmed_unchanged();
    if (strcmp(argv[1], "cgb_speed_key1_readback") == 0) return cgb_speed_key1_readback();
    if (strcmp(argv[1], "cgb_speed_key0_no_switch") == 0) return cgb_speed_key0_no_switch();
    if (strcmp(argv[1], "cgb_speed_cpu_ticks") == 0) {
        int rc = cgb_speed_cpu_ticks();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_cpu_ticks pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_reset_double_speed") == 0) {
        int rc = cgb_speed_reset_double_speed();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_reset_double_speed pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_timer_scaling") == 0) {
        int rc = cgb_speed_timer_scaling();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_timer_scaling pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_serial_scaling") == 0) {
        int rc = cgb_speed_serial_scaling();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_serial_scaling pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_dma_scaling") == 0) {
        int rc = cgb_speed_dma_scaling();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_dma_scaling pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_apu_tap") == 0) {
        int rc = cgb_speed_apu_tap();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_apu_tap pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_remainder_across_switch") == 0) {
        int rc = cgb_speed_remainder_across_switch();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_remainder_across_switch pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_ppu_apu_rtc_unscaled") == 0) {
        int rc = cgb_speed_ppu_apu_rtc_unscaled();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_ppu_apu_rtc_unscaled pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_reset_stall") == 0) {
        int rc = cgb_speed_reset_stall();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_reset_stall pass");
        return rc;
    }
    if (strcmp(argv[1], "cgb_speed_reset_key1") == 0) {
        int rc = cgb_speed_reset_key1();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_reset_key1 pass");
        return rc;
    }
    return 2;
}
