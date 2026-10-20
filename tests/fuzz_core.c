#include "gabbaboy/gabbaboy.h"
#include "gabbaboy_test.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FUZZ_INPUT_LIMIT 65536u
#define FUZZ_OPERATION_LIMIT 16u
#define FUZZ_BATTERY_BYTES 8192u
#define FUZZ_IMPORT_LIMIT (FUZZ_BATTERY_BYTES + 1u)
#define FUZZ_RUN_LIMIT UINT64_C(2048)
#define FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)
#define FUZZ_SPEED_HALF_DOT_LIMIT UINT64_C(600000)
#define FUZZ_CGB_HDMA_OPERATION_LIMIT 16u
#define FUZZ_CGB_HDMA_RUN_LIMIT UINT64_C(16384)
#define FUZZ_CGB_APU_OPERATION_LIMIT 16u
#define FUZZ_CGB_APU_RUN_LIMIT UINT64_C(8192)
#define FUZZ_CGB_APU_SLICE_HALF_DOTS UINT64_C(257)

static void fix_checksum(uint8_t rom[32768]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void make_battery_rom(uint8_t rom[32768]) {
    memset(rom, 0, 32768u);
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    fix_checksum(rom);
}

/* Standalone test build: a violated contract is counted and reported so a deliberately mutated core
 * can be shown to trip an invariant through a numeric exit code (cgb_fuzz_palette_mutant_no_mask).
 * The libFuzzer build aborts, which is what the fuzzer needs to record a crash. */
#ifdef GBB_FUZZ_STANDALONE_TEST
static int contract_failures;
int gbb_fuzz_core_contract_failures(void) { return contract_failures; }
#endif

static void contract_failed(const char *what) {
    fprintf(stderr, "fuzz contract failed: %s\n", what);
#ifdef GBB_FUZZ_STANDALONE_TEST
    ++contract_failures;
#else
    abort();
#endif
}

/* The macro keeps the failing expression and line in the report (a bare abort() preserved this in a
 * core dump; the standalone build has none). */
#define GBB_FUZZ_STR2(x) #x
#define GBB_FUZZ_STR(x) GBB_FUZZ_STR2(x)
#define require_contract(condition) \
    do { if (!(condition)) contract_failed(#condition " at fuzz_core.c:" GBB_FUZZ_STR(__LINE__)); } while (0)

/* Internal test seam, defined by the core and linked into every fuzz target. */
extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);

static struct {
    int selected;
    uint8_t scenario;
    unsigned switches;
    unsigned key1_reads;
    unsigned stop_count;
    unsigned run_calls;
    uint8_t double_speed;
    uint8_t key1_armed;
    uint8_t key1;
    uint32_t stall_half_dots;
    uint32_t mode;
    uint32_t profile;
    uint64_t consumed_half_dots;
    uint64_t master_time_half_dots;
    uint64_t last_trace_time;
    uint32_t path_flags;
    int saw_hram_dma_stop;
    int saw_lcd_off;
} last_speed_observation;

static struct {
    int selected;
    unsigned operations;
    unsigned run_calls;
    uint64_t consumed_half_dots;
} last_hdma_observation;

static struct {
    int selected;
    unsigned operations;
    unsigned run_calls;
    uint64_t consumed_half_dots;
    int terminal;
} last_apu_observation;

#ifdef GBB_FUZZ_STANDALONE_TEST
void gbb_fuzz_core_speed_observation(int *selected, uint8_t *scenario,
                                     unsigned *switches, unsigned *key1_reads,
                                     unsigned *stop_count, unsigned *run_calls,
                                     uint8_t *double_speed, uint8_t *key1_armed,
                                     uint8_t *key1, uint32_t *stall_half_dots,
                                     uint32_t *mode, uint32_t *profile,
                                     uint64_t *consumed_half_dots,
                                     uint64_t *master_time_half_dots,
                                     uint64_t *last_trace_time,
                                     uint32_t *path_flags,
                                     int *saw_hram_dma_stop, int *saw_lcd_off) {
    if (selected != NULL) *selected = last_speed_observation.selected;
    if (scenario != NULL) *scenario = last_speed_observation.scenario;
    if (switches != NULL) *switches = last_speed_observation.switches;
    if (key1_reads != NULL) *key1_reads = last_speed_observation.key1_reads;
    if (stop_count != NULL) *stop_count = last_speed_observation.stop_count;
    if (run_calls != NULL) *run_calls = last_speed_observation.run_calls;
    if (double_speed != NULL) *double_speed = last_speed_observation.double_speed;
    if (key1_armed != NULL) *key1_armed = last_speed_observation.key1_armed;
    if (key1 != NULL) *key1 = last_speed_observation.key1;
    if (stall_half_dots != NULL) *stall_half_dots = last_speed_observation.stall_half_dots;
    if (mode != NULL) *mode = last_speed_observation.mode;
    if (profile != NULL) *profile = last_speed_observation.profile;
    if (consumed_half_dots != NULL)
        *consumed_half_dots = last_speed_observation.consumed_half_dots;
    if (master_time_half_dots != NULL)
        *master_time_half_dots = last_speed_observation.master_time_half_dots;
    if (last_trace_time != NULL) *last_trace_time = last_speed_observation.last_trace_time;
    if (path_flags != NULL) *path_flags = last_speed_observation.path_flags;
    if (saw_hram_dma_stop != NULL)
        *saw_hram_dma_stop = last_speed_observation.saw_hram_dma_stop;
    if (saw_lcd_off != NULL) *saw_lcd_off = last_speed_observation.saw_lcd_off;
}
#endif

/* D-19(4) and D-27: bank indices are fixed on the DMG profile and bounded on the CGB profile no
 * matter what the untrusted input did. */
static void require_banks(const gbb_instance *machine, int cgb) {
    uint8_t vram_bank = 0xA7u;
    uint8_t wram_bank = 0xA7u;
    gbb_test_bank_state(machine, &vram_bank, &wram_bank);
    if (cgb) {
        require_contract(vram_bank <= 1u);
        require_contract(wram_bank >= 1u && wram_bank <= 7u);
    } else {
        require_contract(vram_bank == 0u && wram_bank == 1u);
    }
}

static void fuzz_loader(gbb_instance *machine, const uint8_t *data, size_t size) {
    if (size <= 1u) {
        require_contract(gbb_load_rom(machine, NULL, size) == GBB_INVALID_ARGUMENT);
        return;
    }
    const gbb_error result = gbb_load_rom(machine, data + 1u, size - 1u);
    if (result != GBB_OK) {
        const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
        require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
        require_contract(run.reason == GBB_STOP_BUDGET ||
                         run.reason == GBB_STOP_UNSUPPORTED_BUS ||
                         run.reason == GBB_STOP_INVALID_STATE);
    }
}

static void fuzz_stateful_api(gbb_instance *machine, const uint8_t *data,
                              size_t size, int cgb) {
    uint8_t input[FUZZ_IMPORT_LIMIT];
    uint8_t before[FUZZ_BATTERY_BYTES];
    uint8_t output[FUZZ_BATTERY_BYTES + 2u];
    size_t cursor = 1u;
    uint64_t input_half_dots = 0u;

    for (size_t operation = 0u;
         operation < FUZZ_OPERATION_LIMIT && cursor < size; ++operation) {
        const uint8_t selector = data[cursor++];
        if (selector % 6u == 0u && cursor < size) {
            size_t length = (size_t)(data[cursor++] % 32u);
            if (length > size - cursor) length = size - cursor;
            (void)gbb_load_rom(machine, data + cursor, length);
            cursor += length;
        } else if (selector % 6u == 1u) {
            size_t battery_size = 0u;
            if (gbb_battery_size(machine, &battery_size) != GBB_OK ||
                battery_size != FUZZ_BATTERY_BYTES) continue;
            size_t length = selector == 1u ? FUZZ_BATTERY_BYTES - 1u :
                            selector == 7u ? FUZZ_IMPORT_LIMIT : FUZZ_BATTERY_BYTES;
            memset(input, (int)selector, sizeof(input));
            require_contract(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);
            const gbb_error imported = gbb_import_battery(machine, input, length);
            if (length != FUZZ_BATTERY_BYTES) {
                require_contract(imported == GBB_BATTERY_SIZE_MISMATCH);
                require_contract(gbb_copy_battery(machine, output + 1u,
                                                   sizeof(before)) == GBB_OK);
                require_contract(memcmp(before, output + 1u,
                                        sizeof(before)) == 0);
            } else {
                require_contract(imported == GBB_OK);
            }
        } else if (selector % 6u == 2u) {
            memset(output, 0xA7, sizeof(output));
            (void)gbb_copy_battery(machine, output + 1u,
                                   (selector & 1u) != 0u ?
                                       FUZZ_BATTERY_BYTES - 1u :
                                       sizeof(output) - 2u);
            require_contract(output[0] == 0xA7u);
            require_contract(output[sizeof(output) - 1u] == 0xA7u);
        } else if (selector % 6u == 3u) {
            uint64_t budget = (uint64_t)(selector % 32u) * 64u;
            const uint64_t remaining = FUZZ_INPUT_HALF_DOT_LIMIT - input_half_dots;
            if (budget > remaining) budget = remaining;
            const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
            require_contract(run.consumed_half_dots <= budget);
            input_half_dots += run.consumed_half_dots;
            require_contract(input_half_dots <= FUZZ_INPUT_HALF_DOT_LIMIT);
        } else if (selector % 6u == 4u) {
            (void)gbb_reset(machine);
        } else {
            size_t battery_size = SIZE_MAX;
            const gbb_error result = gbb_battery_size(machine, &battery_size);
            if (result == GBB_NO_BATTERY)
                require_contract(battery_size == SIZE_MAX);
        }
        require_banks(machine, cgb);
    }
}

/* D-28: synthesised-length mode. Only the 0x150-byte header is written; the
 * rest of the one static buffer stays zero, so an 8 MiB + 1 byte load costs no
 * per-input copy. Selector bytes: type, ROM code, RAM code, length class. */
#define FUZZ_MIB (1024u * 1024u)
#define FUZZ_SYNTH_MAX ((size_t)8u * FUZZ_MIB)

static void fuzz_synth_length(gbb_instance *machine, const uint8_t *data,
                              size_t size, int cgb) {
    static uint8_t image[8u * 1024u * 1024u + 1u];
    uint8_t before[FUZZ_BATTERY_BYTES];
    uint8_t after[FUZZ_BATTERY_BYTES];
    size_t before_size = 0u;
    size_t after_size = 0u;

    if (size < 5u) return;
    const uint8_t code = data[2];
    const size_t declared = code <= 8u ? (size_t)32768u << code : (size_t)32768u;
    size_t length = 0u;
    switch (data[4] % 10u) {
    case 0u: length = declared; break;
    case 1u: length = declared - 1u; break;
    case 2u: length = declared + 1u; break;
    case 3u: length = (size_t)2u * FUZZ_MIB; break;
    case 4u: length = (size_t)2u * FUZZ_MIB + 1u; break;
    case 5u: length = (size_t)4u * FUZZ_MIB; break;
    case 6u: length = (size_t)4u * FUZZ_MIB + 1u; break;
    case 7u: length = FUZZ_SYNTH_MAX; break;
    case 8u: length = FUZZ_SYNTH_MAX + 1u; break;
    default: length = SIZE_MAX; break;
    }

    memset(image, 0, 0x150u);
    image[0x147u] = data[1];
    image[0x148u] = code;
    image[0x149u] = data[3];
    /* The CGB profile also sees a fuzzed $143 so PGB-flagged headers are reachable. */
    if (cgb && size > 6u) image[0x143u] = data[6];
    fix_checksum(image);
    if (size > 5u && (data[5] & 1u) != 0u) image[0x14Du] ^= 0xFFu;

    require_contract(gbb_battery_size(machine, &before_size) == GBB_OK &&
                     before_size == FUZZ_BATTERY_BYTES);
    require_contract(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);

    const gbb_error result = gbb_load_rom(machine, image, length);
    require_contract(result == GBB_OK || result == GBB_ROM_TOO_LARGE ||
                     result == GBB_UNSUPPORTED_CARTRIDGE ||
                     result == GBB_UNSUPPORTED_ROM_SIZE ||
                     result == GBB_UNSUPPORTED_RAM_SIZE ||
                     result == GBB_ROM_TRUNCATED ||
                     result == GBB_ROM_SIZE_MISMATCH ||
                     result == GBB_INVALID_ROM ||
                     result == GBB_UNSUPPORTED_CARTRIDGE_VARIANT ||
                     (cgb && result == GBB_UNSUPPORTED_EXECUTION_MODE));
    if (length > FUZZ_SYNTH_MAX) require_contract(result == GBB_ROM_TOO_LARGE);
    if (result != GBB_OK) {
        require_contract(gbb_battery_size(machine, &after_size) == GBB_OK &&
                         after_size == before_size);
        require_contract(gbb_copy_battery(machine, after, sizeof(after)) == GBB_OK);
        require_contract(memcmp(before, after, sizeof(before)) == 0);
    } else {
        const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
        require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
    }
    require_banks(machine, cgb);
}

/* D-27: CGB I/O decode under untrusted guest code. The input becomes up to FUZZ_CGB_OPERATION_LIMIT
 * guest operations, three bytes each: a selector, a value and an address byte. Selector bit 0 makes
 * a read (LDH A,(n)), otherwise a write (LD A,value; LDH (n),A). Selector bit 1 redirects the
 * access to VBK ($FF4F, selector bit 2 set) or SVBK ($FF70) so bank switching is hit often; any
 * other access lands on a fuzzed address in FF00-FF7F. $143 is $80 or $00 from data[1]. */
#define FUZZ_CGB_OPERATION_LIMIT 64u
#define FUZZ_CGB_PROGRAM 0x150u

static void fuzz_cgb_io(gbb_instance *machine, const uint8_t *data, size_t size) {
    static uint8_t rom[32768];
    size_t at = FUZZ_CGB_PROGRAM;
    size_t cursor = 2u;

    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;   /* JP $0150 over the header */
    rom[0x143u] = size > 1u && (data[1] & 1u) != 0u ? 0x80u : 0x00u;
    for (size_t operation = 0u;
         operation < FUZZ_CGB_OPERATION_LIMIT && cursor + 2u < size; ++operation) {
        const uint8_t selector = data[cursor];
        const uint8_t value = data[cursor + 1u];
        uint8_t offset = (uint8_t)(data[cursor + 2u] & 0x7Fu);
        cursor += 3u;
        if ((selector & 2u) != 0u) offset = (selector & 4u) != 0u ? 0x4Fu : 0x70u;
        if ((selector & 1u) != 0u) {
            rom[at++] = 0xF0u; rom[at++] = offset;                 /* LDH A,(n) */
        } else {
            rom[at++] = 0x3Eu; rom[at++] = value;                  /* LD A,value */
            rom[at++] = 0xE0u; rom[at++] = offset;                 /* LDH (n),A */
        }
    }
    rom[at] = 0x76u;                                               /* HALT */
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
    require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
    require_contract(run.reason == GBB_STOP_BUDGET ||
                     run.reason == GBB_STOP_HALTED_IDLE ||
                     run.reason == GBB_STOP_UNSUPPORTED_BUS);
    require_banks(machine, 1);
}

/* D-01/D-22: bounded CGB guest traffic focused on FF51-FF55. Each operation
 * chooses one register and value; the guest run budget and number of run slices
 * are capped independently so hostile lengths cannot create unbounded work. */
static void fuzz_cgb_hdma(gbb_instance *machine, const uint8_t *data, size_t size) {
    static uint8_t rom[32768];
    size_t at = FUZZ_CGB_PROGRAM;
    size_t cursor = 2u;
    unsigned operations = 0u;

    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = size > 1u && (data[1] & 1u) != 0u ? 0x80u : 0xC0u;
    while (operations < FUZZ_CGB_HDMA_OPERATION_LIMIT && cursor + 1u < size) {
        const uint8_t selector = data[cursor++];
        const uint8_t value = data[cursor++];
        const uint8_t offset = (uint8_t)(0x51u + selector % 5u);
        rom[at++] = 0x3Eu; rom[at++] = value;
        rom[at++] = 0xE0u; rom[at++] = offset;
        ++operations;
    }
    rom[at] = 0x76u;
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);

    uint64_t remaining = FUZZ_CGB_HDMA_RUN_LIMIT;
    uint64_t consumed_total = 0u;
    unsigned run_calls = 0u;
    while (remaining != 0u && run_calls < FUZZ_CGB_HDMA_OPERATION_LIMIT) {
        const uint64_t slice = remaining < FUZZ_RUN_LIMIT ? remaining : FUZZ_RUN_LIMIT;
        const gbb_run_result run = gbb_run(machine, slice, NULL, 0u);
        require_contract(run.consumed_half_dots <= slice);
        consumed_total += run.consumed_half_dots;
        remaining -= run.consumed_half_dots;
        ++run_calls;
        if (run.reason == GBB_STOP_UNSUPPORTED_BUS ||
            run.reason == GBB_STOP_INVALID_STATE ||
            run.reason == GBB_STOP_LOCKUP || run.consumed_half_dots == 0u)
            break;
        require_contract(run.reason == GBB_STOP_BUDGET ||
                         run.reason == GBB_STOP_HALTED_IDLE ||
                         run.reason == GBB_STOP_OUTPUT_FULL);
    }
    require_contract(operations <= FUZZ_CGB_HDMA_OPERATION_LIMIT &&
                     run_calls <= FUZZ_CGB_HDMA_OPERATION_LIMIT &&
                     consumed_total <= FUZZ_CGB_HDMA_RUN_LIMIT);
    last_hdma_observation.selected = 1;
    last_hdma_observation.operations = operations;
    last_hdma_observation.run_calls = run_calls;
    last_hdma_observation.consumed_half_dots = consumed_total;
}

#ifdef GBB_FUZZ_STANDALONE_TEST
void gbb_fuzz_core_hdma_observation(int *selected, unsigned *operations,
                                    unsigned *run_calls,
                                    uint64_t *consumed_half_dots) {
    if (selected != NULL) *selected = last_hdma_observation.selected;
    if (operations != NULL) *operations = last_hdma_observation.operations;
    if (run_calls != NULL) *run_calls = last_hdma_observation.run_calls;
    if (consumed_half_dots != NULL)
        *consumed_half_dots = last_hdma_observation.consumed_half_dots;
}

void gbb_fuzz_core_apu_observation(int *selected, unsigned *operations,
                                   unsigned *run_calls,
                                   uint64_t *consumed_half_dots,
                                   int *terminal) {
    if (selected != NULL) *selected = last_apu_observation.selected;
    if (operations != NULL) *operations = last_apu_observation.operations;
    if (run_calls != NULL) *run_calls = last_apu_observation.run_calls;
    if (consumed_half_dots != NULL)
        *consumed_half_dots = last_apu_observation.consumed_half_dots;
    if (terminal != NULL) *terminal = last_apu_observation.terminal;
}
#endif

/* D-20/D-21: hostile APU inputs build a bounded guest program from untrusted byte pairs. The two
 * loader probes are deliberately malformed and must be rejected before replacing the live guest. */
static void fuzz_cgb_apu(gbb_instance *machine, const uint8_t *data, size_t size) {
    static const uint8_t apu_offsets[] = {
        0x26u, 0x12u, 0x24u, 0x25u, 0x1Au, 0x1Cu,
        0x1Du, 0x1Eu, 0x30u, 0x04u, 0x56u
    };
    static uint8_t oversized_rom[32769u];
    uint8_t rom[32768u];
    make_battery_rom(oversized_rom);
    oversized_rom[0x143u] = 0x80u;
    fix_checksum(oversized_rom);
    require_contract(gbb_load_rom(machine, oversized_rom, 0x14Fu) == GBB_ROM_TRUNCATED);
    require_contract(gbb_load_rom(machine, oversized_rom, sizeof(oversized_rom)) ==
                     GBB_ROM_SIZE_MISMATCH);

    make_battery_rom(rom);
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = size > 1u && (data[1] & 1u) != 0u ? 0xC0u : 0x80u;
    size_t at = 0x150u;
    unsigned operations = 0u;
    size_t cursor = 2u;
    while (operations < FUZZ_CGB_APU_OPERATION_LIMIT && cursor + 1u < size) {
        const uint8_t selector = data[cursor++];
        const uint8_t value = data[cursor++];
        rom[at++] = 0x3Eu; rom[at++] = value;
        rom[at++] = 0xE0u; rom[at++] = apu_offsets[selector % sizeof(apu_offsets)];
        ++operations;
    }
    rom[at++] = 0xF0u; rom[at++] = 0x76u; /* Capture PCM12 through the guest bus. */
    rom[at++] = 0xEAu; rom[at++] = 0x00u; rom[at++] = 0xC0u;
    rom[at++] = 0xF0u; rom[at++] = 0x77u; /* Capture PCM34 through the guest bus. */
    rom[at++] = 0xEAu; rom[at++] = 0x01u; rom[at++] = 0xC0u;
    rom[at] = 0x76u;
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);

    uint64_t consumed_total = 0u;
    unsigned run_calls = 0u;
    int terminal = 0;
    while (consumed_total < FUZZ_CGB_APU_RUN_LIMIT &&
           run_calls < FUZZ_CGB_APU_OPERATION_LIMIT) {
        uint64_t budget = FUZZ_CGB_APU_SLICE_HALF_DOTS;
        if (budget > FUZZ_CGB_APU_RUN_LIMIT - consumed_total)
            budget = FUZZ_CGB_APU_RUN_LIMIT - consumed_total;
        const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
        require_contract(run.consumed_half_dots <= budget);
        consumed_total += run.consumed_half_dots;
        ++run_calls;
        if (run.reason == GBB_STOP_HALTED_IDLE) {
            terminal = 1;
            break;
        }
        if (run.reason != GBB_STOP_BUDGET || run.consumed_half_dots == 0u) break;
    }
    require_contract(terminal != 0 && operations <= FUZZ_CGB_APU_OPERATION_LIMIT &&
                     run_calls <= FUZZ_CGB_APU_OPERATION_LIMIT &&
                     consumed_total <= FUZZ_CGB_APU_RUN_LIMIT);
    last_apu_observation.selected = 1;
    last_apu_observation.operations = operations;
    last_apu_observation.run_calls = run_calls;
    last_apu_observation.consumed_half_dots = consumed_total;
    last_apu_observation.terminal = terminal;
}

/* D-27: exercise the real guest KEY1/STOP path under bounded, repeatable inputs. The speed mode has
 * its own budget because a CGB switch stalls for far longer than the ordinary 2,048-half-dot fuzz
 * slice. The private seams below only observe state; all transitions come from guest instructions. */
#define FUZZ_SPEED_PROGRAM 0x150u
#define FUZZ_SPEED_TRACE_CAPACITY 4096u
static gbb_trace_record speed_trace[FUZZ_SPEED_TRACE_CAPACITY];

static size_t speed_emit_a(uint8_t *rom, size_t at, uint8_t value) {
    rom[at++] = 0x3Eu; rom[at++] = value;
    return at;
}

static size_t speed_emit_ldh_write(uint8_t *rom, size_t at, uint8_t offset) {
    rom[at++] = 0xE0u; rom[at++] = offset;
    return at;
}

static size_t speed_emit_absolute_write(uint8_t *rom, size_t at, uint16_t address) {
    rom[at++] = 0xEAu; rom[at++] = (uint8_t)address;
    rom[at++] = (uint8_t)(address >> 8);
    return at;
}

static size_t speed_emit_loop_jump(uint8_t *rom, size_t at, size_t target) {
    const size_t jump_pc = at;
    const int displacement = (int)target - (int)(jump_pc + 2u);
    rom[at++] = 0x18u;
    rom[at++] = (uint8_t)(int8_t)displacement;
    return at;
}

static int speed_switches_on_stop(uint8_t scenario, uint32_t mode) {
    return mode == GBB_MODE_CGB && scenario != 3u;
}

static void speed_apply_last_instruction(const gbb_trace_record *record,
                                         uint8_t scenario, uint32_t mode,
                                         int cgb_profile,
                                         uint8_t *double_speed,
                                         uint8_t *key1_armed,
                                         unsigned *switches) {
    if (cgb_profile && mode == GBB_MODE_CGB &&
        record->opcode[0] == 0xE0u && record->opcode[1] == 0x4Du)
        *key1_armed = (uint8_t)(record->a & 1u);
    if (record->opcode[0] == 0x10u && speed_switches_on_stop(scenario, mode)) {
        *double_speed ^= 1u;
        *key1_armed = 0u;
        ++*switches;
    }
}

static void fuzz_speed(gbb_instance *machine, const uint8_t *data, size_t size,
                       int cgb_profile) {
    uint8_t rom[32768];
    uint8_t scenario = size > 1u ? (uint8_t)(data[1] & 7u) : 0u;
    size_t at = FUZZ_SPEED_PROGRAM;
    size_t key1_store_pc = 0u;
    size_t dma_stop_pc = 0u;
    size_t lcdc_write_pc = 0u;
    size_t ie_write_pc = 0u, if_write_pc = 0u, joyp_write_pc = 0u, dma_start_pc = 0u;
    /* KEY1 is not a guest register on the DMG profile: the cartridge runs in DMG mode, STOP never
     * switches speed, and a woken guest that touches $FF4D stops on an unsupported bus access by
     * design. Scenarios built around KEY1 therefore apply only to the CGB profile; on DMG they
     * fall back to the STOP/wake twin (scenario 7). Scenario 3 (held button) stays as is. */
    if (!cgb_profile && scenario != 3u) scenario = 7u;
    const int switch_expected = cgb_profile && scenario != 3u && scenario != 6u && scenario != 7u;

    memset(&last_speed_observation, 0, sizeof(last_speed_observation));
    last_speed_observation.selected = 1;
    last_speed_observation.scenario = scenario;
    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = cgb_profile && scenario != 6u ? 0x80u : 0x00u;

    if (scenario == 1u) {
        at = speed_emit_a(rom, at, 1u);
        at = speed_emit_ldh_write(rom, at, 0x4Du);
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        const size_t loop = at;
        rom[at++] = 0xF0u; rom[at++] = 0x4Du;
        key1_store_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xC000u);
        at = speed_emit_a(rom, at, 1u);
        at = speed_emit_ldh_write(rom, at, 0x4Du);
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        (void)speed_emit_loop_jump(rom, at, loop);
    } else if (scenario == 2u || scenario == 3u) {
        if (scenario == 3u) {
            at = speed_emit_a(rom, at, 0x20u); /* select the direction-button row */
            joyp_write_pc = at;
            at = speed_emit_ldh_write(rom, at, 0x00u);
        }
        at = speed_emit_a(rom, at, 1u);
        ie_write_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xFFFFu); /* IE = 1, IME stays disabled */
        if_write_pc = at;
        at = speed_emit_ldh_write(rom, at, 0x0Fu);         /* IF = 1 */
        at = speed_emit_a(rom, at, 1u);
        at = speed_emit_ldh_write(rom, at, 0x4Du);
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        const size_t loop = at;
        rom[at++] = 0xF0u; rom[at++] = 0x4Du;
        key1_store_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xC000u);
        (void)speed_emit_loop_jump(rom, at, loop);
    } else if (scenario == 4u) {
        uint8_t stub[16] = {0x3Eu, 0xC0u, 0xE0u, 0x46u, 0x10u, 0x00u,
                            0xF0u, 0x4Du, 0xEAu, 0x00u, 0xC0u, 0x18u, 0u};
        const int8_t back = (int8_t)-7;
        stub[12] = (uint8_t)back;
        dma_start_pc = 0xFF82u;
        dma_stop_pc = 0xFF84u;
        key1_store_pc = 0xFF88u;
        for (size_t i = 0u; i < 13u; ++i) {
            at = speed_emit_a(rom, at, stub[i]);
            at = speed_emit_ldh_write(rom, at, (uint8_t)(0x80u + i));
        }
        at = speed_emit_a(rom, at, 1u);
        at = speed_emit_ldh_write(rom, at, 0x4Du);
        rom[at++] = 0xC3u; rom[at++] = 0x80u; rom[at++] = 0xFFu;
    } else if (scenario == 5u) {
        at = speed_emit_a(rom, at, 0u);
        lcdc_write_pc = at;
        at = speed_emit_ldh_write(rom, at, 0x40u);
        at = speed_emit_a(rom, at, 1u);
        at = speed_emit_ldh_write(rom, at, 0x4Du);
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        const size_t loop = at;
        rom[at++] = 0xF0u; rom[at++] = 0x4Du;
        key1_store_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xC000u);
        (void)speed_emit_loop_jump(rom, at, loop);
    } else if (scenario == 7u) {
        /* DMG twin: KEY1 is not a valid guest register on this profile, so exercise STOP/wake only. */
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        const size_t loop = at;
        rom[at++] = 0x00u;
        (void)speed_emit_loop_jump(rom, at, loop);
    } else {
        at = speed_emit_a(rom, at, 1u);
        at = speed_emit_ldh_write(rom, at, 0x4Du);
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        const size_t loop = at;
        rom[at++] = 0xF0u; rom[at++] = 0x4Du;
        key1_store_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xC000u);
        (void)speed_emit_loop_jump(rom, at, loop);
    }
    (void)at;
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);

    gbb_info info;
    memset(&info, 0, sizeof(info));
    info.struct_size = sizeof(info);
    require_contract(gbb_get_info(machine, &info) == GBB_OK);
    last_speed_observation.mode = info.mode;
    last_speed_observation.profile = info.profile;
    require_contract(info.profile == (cgb_profile ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B));
    if (cgb_profile) {
        const uint32_t expected_mode = scenario == 6u ? GBB_MODE_CGB_DMG_COMPAT : GBB_MODE_CGB;
        require_contract(info.mode == expected_mode);
    }

    if (scenario == 3u) {
        const gbb_input_event press = {0u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_RIGHT};
        require_contract(gbb_queue_events(machine, &press, 1u) == GBB_OK);
    } else if (scenario == 6u || scenario == 7u) {
        const gbb_input_event wake = {256u, GBB_INPUT_STOP_WAKE, 1u};
        require_contract(gbb_queue_events(machine, &wake, 1u) == GBB_OK);
    }

    uint8_t model_speed = 0u, model_armed = 0u;
    uint8_t prior_speed = 0u, prior_armed = 0u;
    uint32_t prior_stall = 0u, dynamic_stall_bound = 0u;
    int have_dynamic_stall_bound = 0;
    int have_prior_instruction = 0, prior_effect_applied = 1;
    gbb_trace_record prior_instruction;
    memset(&prior_instruction, 0, sizeof(prior_instruction));
    uint64_t total_consumed = 0u, last_trace_time = 0u;
    unsigned calls = 0u;
    int key1_inversion_checked = 0;
    const uint64_t initial_clock = gbb_test_master_time_half_dots(machine);
    require_contract(initial_clock == 0u);

    while (total_consumed < FUZZ_SPEED_HALF_DOT_LIMIT && calls < 2048u) {
        const uint8_t entropy = size > 2u ? data[2u + (calls % (size - 2u))] : (uint8_t)(calls + 7u);
        uint64_t budget = ((uint64_t)(entropy & 0x0Fu) + 1u) * 4096u;
        if (budget > FUZZ_SPEED_HALF_DOT_LIMIT - total_consumed)
            budget = FUZZ_SPEED_HALF_DOT_LIMIT - total_consumed;

        const uint64_t before_clock = gbb_test_master_time_half_dots(machine);
        require_contract(before_clock == total_consumed);
        gbb_test_speed_state(machine, &prior_speed, NULL, &prior_stall, &prior_armed);
        if (calls == 0u) { model_speed = prior_speed; model_armed = prior_armed; }
        memset(speed_trace, 0, sizeof(speed_trace));
        const gbb_run_result run = gbb_run(machine, budget, speed_trace,
                                           FUZZ_SPEED_TRACE_CAPACITY);
        ++calls;
        require_contract(run.consumed_half_dots <= budget);
        require_contract(UINT64_MAX - before_clock >= run.consumed_half_dots);
        const uint64_t after_clock = gbb_test_master_time_half_dots(machine);
        require_contract(after_clock >= before_clock);
        require_contract(after_clock - before_clock == run.consumed_half_dots);
        require_contract(UINT64_MAX - total_consumed >= run.consumed_half_dots);
        total_consumed += run.consumed_half_dots;
        require_contract(after_clock == total_consumed);

        info.struct_size = sizeof(info);
        require_contract(gbb_get_info(machine, &info) == GBB_OK);
        uint8_t after_speed = 0u, after_armed = 0u;
        uint32_t after_stall = 0u;
        gbb_test_speed_state(machine, &after_speed, NULL, &after_stall, &after_armed);
        require_contract(after_speed <= 1u && after_armed <= 1u);
        require_contract(info.profile == (cgb_profile ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B));
        if (after_speed != 0u)
            require_contract(info.profile == GBB_PROFILE_CGB_CPU_E && info.mode == GBB_MODE_CGB);
        if (info.mode == GBB_MODE_CGB) require_contract(run.reason != GBB_STOP_STOPPED);
        require_contract((run.reason == GBB_STOP_BUDGET) ||
                         (run.reason == GBB_STOP_TRACE_FULL) ||
                         (run.reason == GBB_STOP_HALTED_IDLE) ||
                         (run.reason == GBB_STOP_STOPPED) ||
                         (run.reason == GBB_STOP_NO_PROGRESS));

        unsigned stop_in_run = 0u;
        for (size_t i = 0u; i < run.trace_count; ++i) {
            const gbb_trace_record *record = &speed_trace[i];
            require_contract(record->time_half_dots >= before_clock);
            require_contract(record->time_half_dots <= after_clock);
            require_contract(record->time_half_dots >= last_trace_time);
            last_trace_time = record->time_half_dots;
            if (have_prior_instruction && !prior_effect_applied) {
                speed_apply_last_instruction(&prior_instruction, scenario, info.mode, cgb_profile,
                                             &model_speed, &model_armed,
                                             &last_speed_observation.switches);
                prior_effect_applied = 1;
            }
            if (record->opcode[0] == 0x10u) {
                ++stop_in_run;
                ++last_speed_observation.stop_count;
                if (scenario == 4u && record->pc == dma_stop_pc)
                    last_speed_observation.saw_hram_dma_stop = 1;
            }
            if (record->opcode[0] == 0xE0u && record->opcode[1] == 0x4Du &&
                record->a == 1u)
                last_speed_observation.path_flags |= 0x01u;
            if ((scenario == 2u || scenario == 3u) && record->pc == ie_write_pc &&
                record->opcode[0] == 0xEAu && record->opcode[1] == 0xFFu &&
                record->opcode[2] == 0xFFu && record->a == 1u)
                last_speed_observation.path_flags |= 0x02u;
            if ((scenario == 2u || scenario == 3u) && record->pc == if_write_pc &&
                record->opcode[0] == 0xE0u && record->opcode[1] == 0x0Fu && record->a == 1u)
                last_speed_observation.path_flags |= 0x04u;
            if (scenario == 3u && record->pc == joyp_write_pc &&
                record->opcode[0] == 0xE0u && record->opcode[1] == 0x00u && record->a == 0x20u)
                last_speed_observation.path_flags |= 0x08u;
            if (scenario == 4u && record->pc == dma_start_pc &&
                record->opcode[0] == 0xE0u && record->opcode[1] == 0x46u && record->a == 0xC0u)
                last_speed_observation.path_flags |= 0x10u;
            if (scenario == 5u && record->pc == lcdc_write_pc &&
                record->opcode[0] == 0xE0u && record->opcode[1] == 0x40u)
                last_speed_observation.saw_lcd_off = 1;
            if (key1_store_pc != 0u && record->pc == key1_store_pc) {
                const uint8_t expected_key1 = cgb_profile && info.mode == GBB_MODE_CGB
                    ? (uint8_t)(0x7Eu | (uint8_t)(model_speed << 7) | model_armed)
                    : 0xFFu;
                ++last_speed_observation.key1_reads;
                last_speed_observation.key1 = record->a;
#ifdef GBB_FUZZ_SPEED_ORACLE_INVERTED
                if (cgb_profile && info.mode == GBB_MODE_CGB && !key1_inversion_checked) {
                    key1_inversion_checked = 1;
                    if (record->a == expected_key1)
                        contract_failed("KEY1 consistency oracle inverted");
                    else
                        require_contract(record->a != expected_key1);
                } else {
                    require_contract(record->a == expected_key1);
                }
#else
                require_contract(record->a == expected_key1);
#endif
            }
            prior_instruction = *record;
            have_prior_instruction = 1;
            prior_effect_applied = 0;
        }
        if (have_prior_instruction && !prior_effect_applied) {
            speed_apply_last_instruction(&prior_instruction, scenario, info.mode, cgb_profile,
                                         &model_speed, &model_armed,
                                         &last_speed_observation.switches);
            prior_effect_applied = 1;
        }
        require_contract(model_speed == after_speed && model_armed == after_armed);

        const int stop_retired = after_speed != prior_speed ||
                                 (prior_armed != 0u && after_armed == 0u) ||
                                 stop_in_run != 0u;
        if (stop_retired) {
            dynamic_stall_bound = after_stall;
            have_dynamic_stall_bound = 1;
        } else {
            require_contract(after_stall <= prior_stall);
            if (have_dynamic_stall_bound) require_contract(after_stall <= dynamic_stall_bound);
        }

        last_speed_observation.double_speed = after_speed;
        last_speed_observation.key1_armed = after_armed;
        last_speed_observation.stall_half_dots = after_stall;
        last_speed_observation.consumed_half_dots = total_consumed;
        last_speed_observation.master_time_half_dots = after_clock;
        last_speed_observation.last_trace_time = last_trace_time;
        ++last_speed_observation.run_calls;
        if (run.consumed_half_dots == 0u) break;
    }

    require_contract(calls != 0u);
    require_contract(last_speed_observation.run_calls == calls);
    require_contract(last_speed_observation.consumed_half_dots == total_consumed);
    require_contract(last_speed_observation.master_time_half_dots == total_consumed);
    if (switch_expected) require_contract(last_speed_observation.switches != 0u);
    require_contract(last_speed_observation.stop_count != 0u);
    if (cgb_profile && scenario != 3u && scenario != 7u)
        require_contract(last_speed_observation.key1_reads != 0u);
    if (scenario == 4u) require_contract(last_speed_observation.saw_hram_dma_stop);
    if (scenario == 5u) require_contract(last_speed_observation.saw_lcd_off);
}

/* D-34: palette RAM and the compatibility palette API under untrusted input. data[0] = 0xA0 | ... on
 * the CGB profile selects this path (bit 6 clear). data[1] bit 0 picks CGB mode ($143 = $80) or
 * compatibility mode ($143 = $00), so the same sequence is read in both. The remaining bytes are up
 * to FUZZ_PALETTE_OPERATION_LIMIT operations of three bytes (selector, a, b):
 *   selector % 8 in 0..4  guest write of `a` to FF68 + selector (BCPS, BCPD, OCPS, OCPD, OPRI)
 *   5                     guest read of FF68 + b % 5
 *   6                     guest write of `a` to LCDC, which toggles the LCD on and off
 *   7                     host action, in order, interleaved with gbb_run slices of the guest:
 *                         a & 3 = 0 run (b + 1) * 256 half-dots; 1 gbb_set_compat_palette with
 *                         struct_size {0, 27, 28, 29, 64}[b % 5] and, when a & 4, bit 15 set on one
 *                         entry; 2 set with a NULL palette; 3 gbb_get_compat_palette.
 * Invariants: every gbb_copy_frame_rgb555 pixel has bit 15 clear, a rejected set leaves the palette
 * unchanged and an accepted one stores exactly what was given. */
#define FUZZ_PALETTE_OPERATION_LIMIT 512u
#define FUZZ_PALETTE_HALF_DOT_LIMIT UINT64_C(400000)
#define FUZZ_PIXELS (160u * 144u)

static uint16_t frame_pixels[FUZZ_PIXELS];

static const uint32_t palette_sizes[5] = {0u, 27u, 28u, 29u, 64u};

typedef union {
    gbb_compat_palette palette;
    uint8_t raw[64];
} palette_buffer;

static int palette_equal(const gbb_compat_palette *a, const gbb_compat_palette *b) {
    return memcmp(a->bg, b->bg, sizeof(a->bg)) == 0 &&
           memcmp(a->obj0, b->obj0, sizeof(a->obj0)) == 0 &&
           memcmp(a->obj1, b->obj1, sizeof(a->obj1)) == 0;
}

static void require_frame_bit15_clear(const gbb_instance *machine) {
    gbb_frame_info info;
    memset(frame_pixels, 0xFF, sizeof(frame_pixels));
    const gbb_error result = gbb_copy_frame_rgb555(machine, frame_pixels, sizeof(frame_pixels),
                                                   160u * 2u, &info);
    if (result != GBB_OK) {
        require_contract(result == GBB_FRAME_NOT_READY);
        return;
    }
    for (size_t i = 0u; i < FUZZ_PIXELS; ++i)
        if (frame_pixels[i] > 0x7FFFu) {
            contract_failed("pixel above 0x7FFF");
            return;
        }
}

static void fuzz_palette_set(gbb_instance *machine, uint8_t a, uint8_t b) {
    palette_buffer given;
    palette_buffer before;
    palette_buffer after;
    memset(&given, 0, sizeof(given));
    uint16_t words[12];
    for (unsigned i = 0u; i < 12u; ++i)
        words[i] = (uint16_t)((b * 0x0101u + i * 0x1357u) & 0x7FFFu);
    if ((a & 4u) != 0u) words[(b >> 3) % 12u] |= 0x8000u;
    memcpy(given.palette.bg, words, 8u);
    memcpy(given.palette.obj0, words + 4, 8u);
    memcpy(given.palette.obj1, words + 8, 8u);
    given.palette.struct_size = palette_sizes[b % 5u];

    memset(&before, 0, sizeof(before));
    before.palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    require_contract(gbb_get_compat_palette(machine, &before.palette) == GBB_OK);

    const int null_palette = (a & 3u) == 2u;
    const gbb_error result = gbb_set_compat_palette(machine, null_palette ? NULL : &given.palette);
    const int bit15 = (a & 4u) != 0u;
    const int should_reject = !null_palette &&
        (given.palette.struct_size < GBB_COMPAT_PALETTE_SIZE_V1 || bit15);
    require_contract(result == (should_reject ? GBB_INVALID_ARGUMENT : GBB_OK));

    memset(&after, 0, sizeof(after));
    after.palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    require_contract(gbb_get_compat_palette(machine, &after.palette) == GBB_OK);
    if (result == GBB_INVALID_ARGUMENT) {
        if (!palette_equal(&before.palette, &after.palette))
            contract_failed("a rejected gbb_set_compat_palette changed the palette");
    } else if (!null_palette) {
        require_contract(palette_equal(&given.palette, &after.palette));
    }
}

static void fuzz_palette(gbb_instance *machine, const uint8_t *data, size_t size) {
    static uint8_t rom[32768];
    uint8_t host[FUZZ_PALETTE_OPERATION_LIMIT][3];
    size_t host_count = 0u;
    size_t at = FUZZ_CGB_PROGRAM;
    size_t cursor = 2u;

    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;   /* JP $0150 over the header */
    rom[0x143u] = size > 1u && (data[1] & 1u) != 0u ? 0x80u : 0x00u;
    for (size_t operation = 0u;
         operation < FUZZ_PALETTE_OPERATION_LIMIT && cursor + 2u < size; ++operation) {
        const uint8_t selector = (uint8_t)(data[cursor] % 8u);
        const uint8_t a = data[cursor + 1u];
        const uint8_t b = data[cursor + 2u];
        cursor += 3u;
        if (selector <= 4u) {
            rom[at++] = 0x3Eu; rom[at++] = a;                          /* LD A,a */
            rom[at++] = 0xE0u; rom[at++] = (uint8_t)(0x68u + selector); /* LDH (n),A */
        } else if (selector == 5u) {
            rom[at++] = 0xF0u; rom[at++] = (uint8_t)(0x68u + b % 5u);  /* LDH A,(n) */
        } else if (selector == 6u) {
            rom[at++] = 0x3Eu; rom[at++] = a;
            rom[at++] = 0xE0u; rom[at++] = 0x40u;                      /* LDH (LCDC),A */
        } else {
            host[host_count][0] = 7u; host[host_count][1] = a; host[host_count][2] = b;
            ++host_count;
        }
    }
    rom[at++] = 0x18u; rom[at] = 0xFEu;                                /* JR -2: time keeps passing */
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);

    uint64_t spent = 0u;
    for (size_t i = 0u; i < host_count; ++i) {
        const uint8_t kind = (uint8_t)(host[i][1] & 3u);
        if (kind == 0u) {
            uint64_t budget = ((uint64_t)host[i][2] + 1u) * 256u;
            if (budget > FUZZ_PALETTE_HALF_DOT_LIMIT - spent)
                budget = FUZZ_PALETTE_HALF_DOT_LIMIT - spent;
            const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
            require_contract(run.consumed_half_dots <= budget);
            spent += run.consumed_half_dots;
        } else if (kind == 3u) {
            palette_buffer out;
            memset(&out, 0, sizeof(out));
            for (size_t k = 0u; k < 3u; ++k) {
                out.palette.struct_size = palette_sizes[(host[i][2] + k) % 5u];
                const gbb_error got = gbb_get_compat_palette(machine, &out.palette);
                const uint32_t asked = palette_sizes[(host[i][2] + k) % 5u];
                if (asked < GBB_COMPAT_PALETTE_SIZE_V1) {
                    require_contract(got == GBB_INVALID_ARGUMENT);
                    require_contract(out.palette.struct_size == asked);
                } else {
                    require_contract(got == GBB_OK);
                    require_contract(out.palette.struct_size == GBB_COMPAT_PALETTE_SIZE_V1);
                }
            }
        } else {
            fuzz_palette_set(machine, host[i][1], host[i][2]);
        }
        require_frame_bit15_clear(machine);
    }
    while (spent < FUZZ_PALETTE_HALF_DOT_LIMIT) {
        uint64_t budget = FUZZ_PALETTE_HALF_DOT_LIMIT - spent;
        if (budget > 65536u) budget = 65536u;
        const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
        require_contract(run.consumed_half_dots <= budget);
        if (run.consumed_half_dots == 0u) break;
        spent += run.consumed_half_dots;
    }
    require_frame_bit15_clear(machine);
    require_banks(machine, 1);
}

/* The DMG profile has no RGB store: the colour copy is refused and writes nothing. */
static void require_dmg_rgb_store_empty(const gbb_instance *machine) {
    gbb_frame_info info;
    memset(frame_pixels, 0xA5, sizeof(frame_pixels));
    require_contract(gbb_copy_frame_rgb555(machine, frame_pixels, sizeof(frame_pixels), 160u * 2u,
                                           &info) == GBB_UNSUPPORTED_PROFILE);
    for (size_t i = 0u; i < FUZZ_PIXELS; ++i)
        if (frame_pixels[i] != 0xA5A5u) {
            contract_failed("DMG profile wrote to the RGB frame buffer");
            return;
        }
}

/* Test-only observer (standalone test build): the profile the most recent input selected, -1 before
 * any input. Lets cgb_fuzz_profile_select prove that bit 7 really reaches gbb_create. */
static int last_profile_cgb = -1;
#ifdef GBB_FUZZ_STANDALONE_TEST
int gbb_fuzz_core_last_profile_cgb(void) { return last_profile_cgb; }
#endif

int gbb_fuzz_core_one_input(const uint8_t *data, size_t size) {
    if (data == NULL || size == 0u || size > FUZZ_INPUT_LIMIT) return 0;
    memset(&last_hdma_observation, 0, sizeof(last_hdma_observation));
    memset(&last_apu_observation, 0, sizeof(last_apu_observation));

    /* data[0] bit 7 selects the profile. Exact 0xD3 selects the APU hostile path; other CGB data
     * with bits 6 or 5 select I/O/palette, while 0x10 in bits 4..6 selects KEY1/STOP. */
    const int cgb = (data[0] & 0x80u) != 0u;
    last_profile_cgb = cgb;
    gbb_instance *machine = NULL;
    require_contract(gbb_create(cgb ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B,
                                &machine) == GBB_OK);
    uint8_t base_rom[32768];
    make_battery_rom(base_rom);
    require_contract(gbb_load_rom(machine, base_rom, sizeof(base_rom)) == GBB_OK);

    if (cgb && data[0] == 0xD3u)
        fuzz_cgb_apu(machine, data, size);
    else if (cgb && data[0] == 0xB0u)
        fuzz_cgb_hdma(machine, data, size);
    else if (cgb && (data[0] & 0x70u) == 0x10u)
        fuzz_speed(machine, data, size, 1);
    else if (!cgb && (data[0] & 0x70u) == 0x10u)
        fuzz_speed(machine, data, size, 0);
    else if (cgb && (data[0] & 0x40u) != 0u)
        fuzz_cgb_io(machine, data, size);
    else if (cgb && (data[0] & 0x20u) != 0u)
        fuzz_palette(machine, data, size);
    else if ((data[0] & 3u) == 2u)
        fuzz_synth_length(machine, data, size, cgb);
    else if ((data[0] & 3u) == 0u)
        fuzz_loader(machine, data, size);
    else
        fuzz_stateful_api(machine, data, size, cgb);
    require_banks(machine, cgb);
    if (!cgb) require_dmg_rgb_store_empty(machine);

    gbb_destroy(machine);
    return 0;
}

#ifndef GBB_FUZZ_STANDALONE_TEST
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    return gbb_fuzz_core_one_input(data, size);
}
#endif
