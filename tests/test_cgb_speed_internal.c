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

static int cgb_speed_stop_cases(void) {
    const uint8_t program[] = {0x10u, 0x3Cu, 0x00u};
    uint8_t rom[32768];
    make_internal_rom(rom, program, sizeof(program));
    gbb_instance *machine = NULL;
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x100u;
    machine->key1_armed = 1u;
    machine->ie = 4u;
    machine->interrupt_flags = 4u;
    machine->a = 0x20u;
    machine->divider_counter = 0x1234u;
    gbb_run_result result = gbb_run(machine, 16u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 16u);
    REQUIRE(machine->double_speed == 1u && machine->key1_armed == 0u);
    REQUIRE(machine->cpu_stall_kind == GBB_STALL_NONE && machine->cpu_stall_half_dots == 0u);
    REQUIRE(machine->divider_counter == 0u && machine->pc >= 0x102u);
    result = gbb_run(machine, 8u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 8u);
    gbb_destroy(machine);

    make_internal_rom(rom, program, sizeof(program));
    REQUIRE(create_internal_machine(rom, &machine) == 0);
    machine->pc = 0x100u;
    machine->key1_armed = 1u;
    machine->ie = 4u;
    machine->interrupt_flags = 4u;
    machine->a = 0u;
    machine->ime_delay = 1u; /* becomes IME-enabled only after STOP retires */
    machine->rom[0x50u] = 0x06u; /* LD B,$42 proves the handler ran */
    machine->rom[0x51u] = 0x42u;
    machine->rom[0x52u] = 0xD9u; /* RETI */
    machine->rom[0x102u] = 0x76u;
    result = gbb_run(machine, 64u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(machine->double_speed == 1u && machine->pc == 0x103u && machine->b == 0x42u);
    gbb_destroy(machine);
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
    if (strcmp(argv[1], "cgb_speed_stop_cases") == 0) {
        int rc = cgb_speed_stop_cases();
        if (rc == 0) puts("cgb-speed-internal cgb_speed_stop_cases pass");
        return rc;
    }
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
