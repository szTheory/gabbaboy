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
#define FUZZ_STATE_TAG 0xF0u
#define FUZZ_STATE_ROM_BYTES 32768u
#define FUZZ_STATE_RAM_BYTES 8192u
#define FUZZ_STATE_HEADER_BYTES 64u
#define FUZZ_STATE_WIRE_LIMIT 524352u
#define FUZZ_STATE_INSTANCE_BYTES_LIMIT (1024u * 1024u)
#define FUZZ_STATE_OPERATION_LIMIT 16u
#define FUZZ_STATE_RUN_HALF_DOT_LIMIT UINT64_C(2048)
#define FUZZ_STATE_EVENT_CAPACITY 64u
#define FUZZ_STATE_MAX_RAM_BYTES 131072u
#define FUZZ_STATE_OFFSET_ADJUSTMENT (FUZZ_STATE_MAX_RAM_BYTES - FUZZ_STATE_RAM_BYTES)
#define FUZZ_STATE_BODY_OFFSET(max_ram_offset) ((size_t)(max_ram_offset) - FUZZ_STATE_OFFSET_ADJUSTMENT)
#define FUZZ_STATE_BODY_OFFSET_RTC_SECONDS FUZZ_STATE_BODY_OFFSET(131078u)
#define FUZZ_STATE_BODY_OFFSET_RTC_MINUTES FUZZ_STATE_BODY_OFFSET(131079u)
#define FUZZ_STATE_BODY_OFFSET_RTC_HOURS FUZZ_STATE_BODY_OFFSET(131080u)
#define FUZZ_STATE_BODY_OFFSET_RTC_SYNC FUZZ_STATE_BODY_OFFSET(131093u)
#define FUZZ_STATE_BODY_OFFSET_BG_CRAM FUZZ_STATE_BODY_OFFSET(180558u)
#define FUZZ_STATE_BODY_OFFSET_TIMER_RELOADED FUZZ_STATE_BODY_OFFSET(319123u)
#define FUZZ_STATE_BODY_OFFSET_INSTRUCTION_START FUZZ_STATE_BODY_OFFSET(319131u)
#define FUZZ_STATE_BODY_OFFSET_TIME FUZZ_STATE_BODY_OFFSET(319155u)
#define FUZZ_STATE_BODY_OFFSET_INPUT_COUNT FUZZ_STATE_BODY_OFFSET(319163u)
#define FUZZ_STATE_BODY_OFFSET_INPUT_AT FUZZ_STATE_BODY_OFFSET(319164u)
#define FUZZ_STATE_BODY_OFFSET_INPUT_KIND FUZZ_STATE_BODY_OFFSET(319676u)
#define FUZZ_STATE_BODY_OFFSET_INPUT_VALUE FUZZ_STATE_BODY_OFFSET(319740u)
#define FUZZ_STATE_BODY_OFFSET_APU_SAMPLE_PHASE FUZZ_STATE_BODY_OFFSET(319895u)
#define FUZZ_STATE_BODY_OFFSET_AUDIO_RING FUZZ_STATE_BODY_OFFSET(319903u)
#define FUZZ_STATE_BODY_OFFSET_AUDIO_HEAD FUZZ_STATE_BODY_OFFSET(320159u)
#define FUZZ_STATE_BODY_OFFSET_AUDIO_HPF_OUTPUT FUZZ_STATE_BODY_OFFSET(320176u)
#define FUZZ_STATE_HORIZON (UINT64_C(1) << 62)
#define FUZZ_STATE_WITNESS_HEADER_ONLY (1u << 0)
#define FUZZ_STATE_WITNESS_LATE_INVALID (1u << 1)
#define FUZZ_STATE_WITNESS_PREMATURE_APPLY (1u << 2)
#define FUZZ_STATE_WITNESS_NO_WRITE (1u << 3)
#define FUZZ_STATE_WITNESS_CAP_SENTINEL (1u << 4)
#define FUZZ_STATE_WITNESS_SIGNED_AUDIO (1u << 5)
#define FUZZ_STATE_WITNESS_QUEUE_ORDER (1u << 6)
#define FUZZ_STATE_WITNESS_RTC_PALETTE (1u << 7)
#define FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE (1u << 8)
#define FUZZ_STATE_WITNESS_TARGET (1u << 9)

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
extern size_t gbb_test_instance_bytes_size(void);
extern gbb_error gbb_test_copy_instance_bytes(const gbb_instance *, uint8_t *, size_t);

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

static struct {
    int selected;
    uint8_t profile_selector;
    uint8_t scenario;
    unsigned operations;
    uint32_t witness;
} last_state_observation;
static uint32_t state_witnesses_seen;

#ifdef GBB_FUZZ_STANDALONE_TEST
#define GBB_FUZZ_SPEED_MUTATION_DMG_ROUTE 1u
#define GBB_FUZZ_SPEED_MUTATION_DROP_HELD_OBSERVATION 2u
#define GBB_FUZZ_SPEED_MUTATION_DROP_WAKE_OBSERVATION 3u
static unsigned speed_mutation;
void gbb_fuzz_core_set_speed_mutation(unsigned mutation) { speed_mutation = mutation; }
#endif

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

/* Scenario 7 never writes KEY1, so its STOP is unarmed: on a CGB-mode cartridge that is the ordinary
 * low-power STOP (Pan Docs CGB Registers, docs/cgb-profile.md "STOP with KEY1 armed"), not a switch. */
static int speed_switches_on_stop(uint8_t scenario, uint32_t mode) {
    return mode == GBB_MODE_CGB && scenario != 3u && scenario != 7u;
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
    size_t joyp_read_pc = 0u;
    size_t post_wake_store_pc = 0u;
    /* KEY1 is not a guest register on DMG. CGB-only speed scenarios fall back to the STOP/wake
     * twin; held-button scenario 3 has its own DMG STOP/wake program without KEY1 accesses. */
    if (!cgb_profile && scenario != 3u) scenario = 7u;
    const int switch_expected = cgb_profile && scenario != 3u && scenario != 6u && scenario != 7u;
    int dmg_held_path = !cgb_profile && scenario == 3u;
#ifdef GBB_FUZZ_STANDALONE_TEST
    if (speed_mutation == GBB_FUZZ_SPEED_MUTATION_DMG_ROUTE) dmg_held_path = 0;
#endif

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
    } else if (dmg_held_path) {
        at = speed_emit_a(rom, at, 0x20u); /* select the direction-button row */
        joyp_write_pc = at;
        at = speed_emit_ldh_write(rom, at, 0x00u);
        at = speed_emit_a(rom, at, 0x10u);
        ie_write_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xFFFFu); /* enable the joypad interrupt */
        at = speed_emit_a(rom, at, 0u);
        if_write_pc = at;
        at = speed_emit_ldh_write(rom, at, 0x0Fu); /* clear pending interrupts before STOP */
        rom[at++] = 0x10u; rom[at++] = 0x00u;
        joyp_read_pc = at;
        rom[at++] = 0xF0u; rom[at++] = 0x00u; /* wake, then observe the held direction button */
        post_wake_store_pc = at;
        at = speed_emit_absolute_write(rom, at, 0xC000u);
        const size_t loop = at;
        rom[at++] = 0x00u;
        (void)speed_emit_loop_jump(rom, at, loop);
    } else if (scenario == 2u || scenario == 3u) {
        if (scenario == 3u) {
            at = speed_emit_a(rom, at, 0x20u); /* select the direction-button row */
            joyp_write_pc = at;
            at = speed_emit_ldh_write(rom, at, 0x00u);
            joyp_read_pc = at;
            rom[at++] = 0xF0u; rom[at++] = 0x00u; /* observe the held direction button */
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
        if (!cgb_profile) {
            const gbb_input_event wake = {256u, GBB_INPUT_STOP_WAKE, 1u};
            require_contract(gbb_queue_events(machine, &wake, 1u) == GBB_OK);
        }
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
    int stop_seen = 0;
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
        if (info.mode == GBB_MODE_CGB && scenario != 7u)
            require_contract(run.reason != GBB_STOP_STOPPED);
        require_contract((run.reason == GBB_STOP_BUDGET) ||
                         (run.reason == GBB_STOP_TRACE_FULL) ||
                         (run.reason == GBB_STOP_HALTED_IDLE) ||
                         (run.reason == GBB_STOP_STOPPED) ||
                         (run.reason == GBB_STOP_NO_PROGRESS)
#ifdef GBB_FUZZ_STANDALONE_TEST
                         || (speed_mutation == GBB_FUZZ_SPEED_MUTATION_DMG_ROUTE &&
                             !cgb_profile && scenario == 3u && !dmg_held_path &&
                             run.reason == GBB_STOP_UNSUPPORTED_BUS)
#endif
                         );

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
                stop_seen = 1;
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
#ifdef GBB_FUZZ_STANDALONE_TEST
            const int record_held_observation =
                speed_mutation != GBB_FUZZ_SPEED_MUTATION_DROP_HELD_OBSERVATION;
            const int record_wake_observation =
                speed_mutation != GBB_FUZZ_SPEED_MUTATION_DROP_WAKE_OBSERVATION;
#else
            const int record_held_observation = 1;
            const int record_wake_observation = 1;
#endif
            if (record_held_observation && scenario == 3u && record->pc == joyp_read_pc &&
                record->opcode[0] == 0xF0u && record->opcode[1] == 0x00u &&
                (record->a & 0x01u) == 0u)
                last_speed_observation.path_flags |= 0x20u;
            if (record_wake_observation && scenario == 3u && dmg_held_path && stop_seen &&
                record->pc == post_wake_store_pc && record->opcode[0] == 0xEAu &&
                record->opcode[1] == 0x00u && record->opcode[2] == 0xC0u)
                last_speed_observation.path_flags |= 0x40u;
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

static uint32_t fuzz_state_read_u32le(const uint8_t *bytes) {
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

static uint64_t fuzz_state_read_u64le(const uint8_t *bytes) {
    uint64_t value = 0u;
    for (unsigned int i = 0u; i < 8u; ++i) value |= (uint64_t)bytes[i] << (8u * i);
    return value;
}

static void fuzz_state_write_u32le(uint8_t *bytes, uint32_t value) {
    for (unsigned int i = 0u; i < 4u; ++i) bytes[i] = (uint8_t)(value >> (8u * i));
}

static void fuzz_state_write_u64le(uint8_t *bytes, uint64_t value) {
    for (unsigned int i = 0u; i < 8u; ++i) bytes[i] = (uint8_t)(value >> (8u * i));
}

static uint32_t fuzz_state_crc32_update(uint32_t crc, const uint8_t *bytes, size_t size) {
    for (size_t i = 0u; i < size; ++i) {
        crc ^= bytes[i];
        for (unsigned int bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) ? UINT32_C(0xEDB88320) : 0u);
    }
    return crc;
}

static int fuzz_state_rechecksum(uint8_t *state, size_t state_size) {
    if (state == NULL || state_size < FUZZ_STATE_HEADER_BYTES ||
        state_size > FUZZ_STATE_WIRE_LIMIT) return 0;
    const uint32_t body_size = fuzz_state_read_u32le(state + 52u);
    const uint32_t total_size = fuzz_state_read_u32le(state + 56u);
    if (total_size != state_size || body_size != state_size - FUZZ_STATE_HEADER_BYTES) return 0;
    uint32_t crc = fuzz_state_crc32_update(UINT32_MAX, state, 60u);
    crc = fuzz_state_crc32_update(crc, state + FUZZ_STATE_HEADER_BYTES, body_size) ^ UINT32_MAX;
    fuzz_state_write_u32le(state + 60u, crc);
    return 1;
}

static void fuzz_state_mark_witness(uint32_t witness, const char *name) {
    last_state_observation.witness |= witness;
    if ((state_witnesses_seen & witness) == 0u) {
        fprintf(stderr, "state-fuzz-witness: %s\n", name);
        state_witnesses_seen |= witness;
    }
}

#ifdef GBB_FUZZ_STANDALONE_TEST
void gbb_fuzz_core_state_observation(int *selected, uint8_t *profile_selector,
                                     uint8_t *scenario, unsigned *operations,
                                     uint32_t *witness, uint32_t *witnesses_seen) {
    if (selected != NULL) *selected = last_state_observation.selected;
    if (profile_selector != NULL) *profile_selector = last_state_observation.profile_selector;
    if (scenario != NULL) *scenario = last_state_observation.scenario;
    if (operations != NULL) *operations = last_state_observation.operations;
    if (witness != NULL) *witness = last_state_observation.witness;
    if (witnesses_seen != NULL) *witnesses_seen = state_witnesses_seen;
}
#endif

/* Format-v1 body offsets are the compiled field-census offsets for a maximum-RAM cartridge,
 * adjusted to the synthetic MBC3 fixture's 8 KiB RAM. state_fuzz_controls rechecks these against
 * the private compiled census, so field reordering cannot silently turn semantic mutations shallow. */
int gbb_fuzz_state_one_input(const uint8_t *data, size_t size) {
    if (data == NULL || size < 3u || size > FUZZ_INPUT_LIMIT || data[0] != FUZZ_STATE_TAG) return 0;

    memset(&last_state_observation, 0, sizeof(last_state_observation));
    last_state_observation.selected = 1;
    uint8_t profile_selector = (uint8_t)(data[1] % 3u);
    const uint8_t scenario = (uint8_t)(data[2] % 8u);
    if (scenario == 6u) profile_selector = 2u; /* Palette bytes are exercised in native CGB mode. */
    last_state_observation.profile_selector = profile_selector;
    last_state_observation.scenario = scenario;
    fuzz_state_mark_witness(FUZZ_STATE_WITNESS_TARGET, "state-load-target");

    gbb_instance *machine = NULL;
    uint8_t rom[FUZZ_STATE_ROM_BYTES];
    uint8_t *snapshot = NULL, *mutated = NULL, *resaved = NULL;
    uint8_t *instance_before = NULL, *instance_after = NULL;
    uint8_t *battery_before = NULL, *battery_after = NULL;
    size_t state_size = 0u, battery_size = 0u, instance_bytes_size = 0u;
    uint64_t battery_generation_before = 0u;
    unsigned int operations = 0u;
    int ok = 0;

#define FUZZ_STATE_REQUIRE(condition, reason) do { \
    if (!(condition)) { contract_failed(reason); goto fuzz_state_cleanup; } \
} while (0)
#define FUZZ_STATE_OPERATION() do { \
    ++operations; \
    FUZZ_STATE_REQUIRE(operations <= FUZZ_STATE_OPERATION_LIMIT, \
                       "state semantic target exceeded its per-input operation bound"); \
} while (0)

    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x00u; rom[0x102u] = 0x02u;
    rom[0x143u] = profile_selector == 2u ? 0x80u : 0x00u;
    rom[0x147u] = 0x10u; /* MBC3 timer + 8 KiB RAM + battery. */
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    rom[0x200u] = 0x18u; rom[0x201u] = 0xFEu; /* Bounded JR -2 loop. */
    fix_checksum(rom);

    const gbb_profile profile = profile_selector == 0u
        ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E;
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_create(profile, &machine) == GBB_OK,
                       "state semantic fixture creation failed");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK,
                       "state semantic synthetic ROM load failed");
    FUZZ_STATE_OPERATION();
    const gbb_run_result initial_run = gbb_run(machine, FUZZ_STATE_RUN_HALF_DOT_LIMIT, NULL, 0u);
    FUZZ_STATE_REQUIRE(initial_run.consumed_half_dots <= FUZZ_STATE_RUN_HALF_DOT_LIMIT &&
                       (initial_run.reason == GBB_STOP_BUDGET ||
                        initial_run.reason == GBB_STOP_HALTED_IDLE),
                       "state semantic fixture run exceeded its bounded domain");

    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_state_size(machine, &state_size) == GBB_OK &&
                       state_size >= FUZZ_STATE_HEADER_BYTES &&
                       state_size <= FUZZ_STATE_WIRE_LIMIT,
                       "state semantic fixture size is outside the public wire bound");
    snapshot = (uint8_t *)malloc(state_size);
    mutated = (uint8_t *)malloc(state_size);
    resaved = (uint8_t *)malloc(state_size);
    FUZZ_STATE_REQUIRE(snapshot != NULL && mutated != NULL && resaved != NULL,
                       "state semantic fixture buffer allocation failed");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_save_state(machine, snapshot, state_size) == GBB_OK,
                       "state semantic fixture save failed");
    instance_bytes_size = gbb_test_instance_bytes_size();
    FUZZ_STATE_REQUIRE(instance_bytes_size != 0u &&
                       instance_bytes_size <= FUZZ_STATE_INSTANCE_BYTES_LIMIT,
                       "state semantic instance snapshot exceeds its one-MiB caller-owned bound");
    instance_before = (uint8_t *)malloc(instance_bytes_size);
    instance_after = (uint8_t *)malloc(instance_bytes_size);
    FUZZ_STATE_REQUIRE(instance_before != NULL && instance_after != NULL,
                       "state semantic instance snapshot allocation failed");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_test_copy_instance_bytes(machine, instance_before,
                                                     instance_bytes_size) == GBB_OK,
                       "state semantic whole-instance snapshot failed");
    FUZZ_STATE_REQUIRE(fuzz_state_read_u32le(snapshot + 56u) == state_size &&
                       fuzz_state_read_u32le(snapshot + 52u) ==
                           state_size - FUZZ_STATE_HEADER_BYTES &&
                       (uint16_t)(snapshot[4] | ((uint16_t)snapshot[5] << 8)) == 1u,
                       "state semantic fixture is not the qualified format-v1 body");
    const size_t body_size = state_size - FUZZ_STATE_HEADER_BYTES;
    FUZZ_STATE_REQUIRE(FUZZ_STATE_BODY_OFFSET_AUDIO_HPF_OUTPUT + 8u <= body_size &&
                       FUZZ_STATE_BODY_OFFSET_RTC_SYNC + 8u <= body_size &&
                       FUZZ_STATE_BODY_OFFSET_BG_CRAM + 2u <= body_size &&
                       FUZZ_STATE_BODY_OFFSET_INPUT_VALUE + FUZZ_STATE_EVENT_CAPACITY <= body_size,
                       "state semantic offsets exceed the compiled synthetic state body");

    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_battery_size(machine, &battery_size) == GBB_OK &&
                       battery_size == FUZZ_STATE_RAM_BYTES + GBB_RTC_BLOCK_SIZE,
                       "MBC3 battery image does not cover all 8 KiB of owned RAM and RTC bytes");
    battery_before = (uint8_t *)malloc(battery_size);
    battery_after = (uint8_t *)malloc(battery_size);
    FUZZ_STATE_REQUIRE(battery_before != NULL && battery_after != NULL,
                       "state semantic battery buffer allocation failed");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_copy_battery(machine, battery_before, battery_size) == GBB_OK,
                       "state semantic battery snapshot failed");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_battery_generation(machine, &battery_generation_before) == GBB_OK,
                       "state semantic battery generation query failed");

    memcpy(mutated, snapshot, state_size);
    uint8_t *body = mutated + FUZZ_STATE_HEADER_BYTES;
    const uint8_t value0 = size > 3u ? data[3] : 0u;
    const uint8_t value1 = size > 4u ? data[4] : 0u;
    const uint8_t value2 = size > 5u ? data[5] : 0u;
    const uint8_t value3 = size > 6u ? data[6] : 0u;
    uint8_t expected_refusal = 0u;

    switch (scenario) {
        case 0u: /* Shallow header-only control: no checksum repair or body change. */
            mutated[0] ^= 0x80u;
            expected_refusal = 1u;
            break;
        case 1u: /* Late ordinary-time cap violation, with a repaired CRC. */
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_TIME,
                                   FUZZ_STATE_HORIZON + 1u + value0);
            expected_refusal = 2u;
            break;
        case 2u: /* Last-field range failure catches any premature application. */
            fuzz_state_write_u32le(body + FUZZ_STATE_BODY_OFFSET_AUDIO_HPF_OUTPUT,
                                   UINT32_C(0x80000000) | ((uint32_t)value0 << 8));
            expected_refusal = 3u;
            break;
        case 3u: /* Accepted exact-cap time plus the validated timer sentinel. */
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_TIME, FUZZ_STATE_HORIZON);
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_INSTRUCTION_START,
                                   FUZZ_STATE_HORIZON);
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_RTC_SYNC,
                                   FUZZ_STATE_HORIZON);
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_TIMER_RELOADED, UINT64_MAX);
            break;
        case 4u: { /* A negative signed event value in a slot with nonzero lifetime. */
            const uint8_t head = body[FUZZ_STATE_BODY_OFFSET_AUDIO_HEAD] & 0x0Fu;
            const size_t slot = ((size_t)head + 15u) % 16u;
            const int64_t edge = -(int64_t)(1u + (value0 & 0x7Fu));
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_AUDIO_RING + slot * 8u,
                                   (uint64_t)edge);
            break;
        }
        case 5u: { /* Equal-time press then release retains caller ordering. */
            const uint64_t now = fuzz_state_read_u64le(body + FUZZ_STATE_BODY_OFFSET_TIME);
            FUZZ_STATE_REQUIRE(now <= FUZZ_STATE_HORIZON - 16u,
                               "state queue fixture has no room for its bounded events");
            body[FUZZ_STATE_BODY_OFFSET_INPUT_COUNT] = 2u;
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_INPUT_AT, now + 8u);
            fuzz_state_write_u64le(body + FUZZ_STATE_BODY_OFFSET_INPUT_AT + 8u, now + 8u);
            body[FUZZ_STATE_BODY_OFFSET_INPUT_KIND] = (uint8_t)GBB_INPUT_BUTTON_PRESS;
            body[FUZZ_STATE_BODY_OFFSET_INPUT_KIND + 1u] = (uint8_t)GBB_INPUT_BUTTON_RELEASE;
            body[FUZZ_STATE_BODY_OFFSET_INPUT_VALUE] = (uint8_t)(value0 & 7u);
            body[FUZZ_STATE_BODY_OFFSET_INPUT_VALUE + 1u] = (uint8_t)(value1 & 7u);
            break;
        }
        case 6u: /* MBC3 RTC and native CGB palette state are both semantic fields. */
            body[FUZZ_STATE_BODY_OFFSET_RTC_SECONDS] = (uint8_t)(value0 % 60u);
            body[FUZZ_STATE_BODY_OFFSET_RTC_MINUTES] = (uint8_t)(value1 % 60u);
            body[FUZZ_STATE_BODY_OFFSET_RTC_HOURS] = (uint8_t)(value2 % 24u);
            body[FUZZ_STATE_BODY_OFFSET_BG_CRAM] = value3;
            body[FUZZ_STATE_BODY_OFFSET_BG_CRAM + 1u] = (uint8_t)(value0 & 0x7Fu);
            break;
        case 7u: /* The saved valid state is still a fuzzed accepted-load closure case. */
            break;
    }
    if (scenario != 0u)
        FUZZ_STATE_REQUIRE(fuzz_state_rechecksum(mutated, state_size),
                           "state semantic CRC repair failed");

    FUZZ_STATE_OPERATION();
    const gbb_error load_result = gbb_load_state(machine, mutated, state_size);
    if (expected_refusal != 0u) {
        const gbb_error expected_error = expected_refusal == 1u
            ? GBB_STATE_BAD_FORMAT : GBB_STATE_INVALID_CONTENT;
        FUZZ_STATE_REQUIRE(load_result == expected_error,
                           "state semantic refusal did not reach its intended validator");
        FUZZ_STATE_OPERATION();
        FUZZ_STATE_REQUIRE(gbb_test_copy_instance_bytes(machine, instance_after,
                                                         instance_bytes_size) == GBB_OK &&
                           memcmp(instance_before, instance_after,
                                  instance_bytes_size) == 0,
                           "refused state load changed opaque instance bytes or excluded observers");
        FUZZ_STATE_OPERATION();
        FUZZ_STATE_REQUIRE(gbb_save_state(machine, resaved, state_size) == GBB_OK &&
                           memcmp(snapshot, resaved, state_size) == 0,
                           "refused state load changed serialized instance state");
        FUZZ_STATE_OPERATION();
        FUZZ_STATE_REQUIRE(gbb_copy_battery(machine, battery_after, battery_size) == GBB_OK &&
                           memcmp(battery_before, battery_after, battery_size) == 0,
                           "refused state load changed owned battery RAM or RTC data");
        uint64_t battery_generation_after = 0u;
        FUZZ_STATE_OPERATION();
        FUZZ_STATE_REQUIRE(gbb_battery_generation(machine, &battery_generation_after) == GBB_OK &&
                           battery_generation_after == battery_generation_before,
                           "refused state load changed battery generation");
        fuzz_state_mark_witness(FUZZ_STATE_WITNESS_NO_WRITE, "no-write-refusal");
        if (expected_refusal == 1u)
            fuzz_state_mark_witness(FUZZ_STATE_WITNESS_HEADER_ONLY, "header-only-control");
        else if (expected_refusal == 2u)
            fuzz_state_mark_witness(FUZZ_STATE_WITNESS_LATE_INVALID, "late-invalid-field");
        else
            fuzz_state_mark_witness(FUZZ_STATE_WITNESS_PREMATURE_APPLY,
                                    "premature-apply-refusal");
        goto fuzz_state_success;
    }

    FUZZ_STATE_REQUIRE(load_result == GBB_OK,
                       "accepted semantic state seed was rejected after CRC repair");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_save_state(machine, resaved, state_size) == GBB_OK &&
                       memcmp(mutated, resaved, state_size) == 0,
                       "accepted hostile state did not canonical-resave identically");

    if (scenario == 3u) {
        FUZZ_STATE_REQUIRE(fuzz_state_read_u64le(body + FUZZ_STATE_BODY_OFFSET_TIME) ==
                               FUZZ_STATE_HORIZON &&
                           fuzz_state_read_u64le(body + FUZZ_STATE_BODY_OFFSET_TIMER_RELOADED) ==
                               UINT64_MAX,
                           "accepted cap/sentinel fixture lost its extreme fields");
    }

    FUZZ_STATE_OPERATION();
    const gbb_run_result bounded_run = gbb_run(machine, 32u, NULL, 0u);
    const int bounded_run_valid = bounded_run.consumed_half_dots <= 32u &&
                       (scenario == 3u
                           ? (bounded_run.reason == GBB_STOP_NO_PROGRESS &&
                              bounded_run.consumed_half_dots == 0u)
                           : (bounded_run.reason == GBB_STOP_BUDGET ||
                              bounded_run.reason == GBB_STOP_HALTED_IDLE));
    if (!bounded_run_valid)
        fprintf(stderr, "state fuzz run result scenario=%u reason=%u consumed=%llu\n",
                scenario, (unsigned int)bounded_run.reason,
                (unsigned long long)bounded_run.consumed_half_dots);
    FUZZ_STATE_REQUIRE(bounded_run_valid,
                       "accepted state violated bounded run or exact-cap closure");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_save_state(machine, resaved, state_size) == GBB_OK,
                       "accepted post-run state save failed");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_load_state(machine, resaved, state_size) == GBB_OK,
                       "accepted post-run state could not reload");
    FUZZ_STATE_OPERATION();
    FUZZ_STATE_REQUIRE(gbb_save_state(machine, mutated, state_size) == GBB_OK &&
                       memcmp(resaved, mutated, state_size) == 0,
                       "accepted post-run reload/resave did not close canonically");
    if (scenario == 3u)
        fuzz_state_mark_witness(FUZZ_STATE_WITNESS_CAP_SENTINEL, "cap-sentinel");
    else if (scenario == 4u)
        fuzz_state_mark_witness(FUZZ_STATE_WITNESS_SIGNED_AUDIO, "signed-audio-edge");
    else if (scenario == 5u)
        fuzz_state_mark_witness(FUZZ_STATE_WITNESS_QUEUE_ORDER, "queue-ordering");
    else if (scenario == 6u)
        fuzz_state_mark_witness(FUZZ_STATE_WITNESS_RTC_PALETTE, "rtc-palette");
    fuzz_state_mark_witness(FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE,
                            "accepted-state-closure");

fuzz_state_success:
    last_state_observation.operations = operations;
    ok = 1;
fuzz_state_cleanup:
    free(battery_after);
    free(battery_before);
    free(instance_after);
    free(instance_before);
    free(resaved);
    free(mutated);
    free(snapshot);
    if (machine != NULL) gbb_destroy(machine);
#undef FUZZ_STATE_OPERATION
#undef FUZZ_STATE_REQUIRE
    return ok ? 0 : 1;
}

int gbb_fuzz_core_one_input(const uint8_t *data, size_t size) {
    memset(&last_speed_observation, 0, sizeof(last_speed_observation));
    memset(&last_state_observation, 0, sizeof(last_state_observation));
    last_profile_cgb = -1;
    if (data == NULL || size == 0u || size > FUZZ_INPUT_LIMIT) return 0;
    memset(&last_hdma_observation, 0, sizeof(last_hdma_observation));
    memset(&last_apu_observation, 0, sizeof(last_apu_observation));

    if (data[0] == FUZZ_STATE_TAG) return gbb_fuzz_state_one_input(data, size);

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

#if defined(GBB_FUZZ_STANDALONE_TEST) && defined(GBB_STATE_FUZZ_STANDALONE_MAIN)
static int run_state_fuzz_snapshot_api_controls(void) {
    const size_t size = gbb_test_instance_bytes_size();
    if (size == 0u || size > FUZZ_STATE_INSTANCE_BYTES_LIMIT) {
        fprintf(stderr, "state snapshot seam size is outside its one-MiB bound\n");
        return 1;
    }
    uint8_t *bytes = (uint8_t *)malloc(size);
    gbb_instance *machine = NULL;
    if (bytes == NULL || gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) {
        fprintf(stderr, "state snapshot seam control setup failed\n");
        free(bytes);
        gbb_destroy(machine);
        return 1;
    }
    memset(bytes, 0xA5, size);
    if (gbb_test_copy_instance_bytes(NULL, bytes, size) != GBB_INVALID_ARGUMENT) {
        fprintf(stderr, "state snapshot seam accepted a NULL instance or wrote on refusal\n");
        free(bytes);
        gbb_destroy(machine);
        return 1;
    }
    int unchanged = 1;
    for (size_t i = 0u; i < size; ++i) unchanged &= bytes[i] == 0xA5u;
    if (!unchanged ||
        gbb_test_copy_instance_bytes(machine, NULL, size) != GBB_INVALID_ARGUMENT) {
        fprintf(stderr, "state snapshot seam accepted a NULL output or wrote on refusal\n");
        free(bytes);
        gbb_destroy(machine);
        return 1;
    }
    if (gbb_test_copy_instance_bytes(machine, bytes, size - 1u) != GBB_INVALID_ARGUMENT) {
        fprintf(stderr, "state snapshot seam accepted a short caller buffer\n");
        free(bytes);
        gbb_destroy(machine);
        return 1;
    }
    unchanged = 1;
    for (size_t i = 0u; i < size; ++i) unchanged &= bytes[i] == 0xA5u;
    if (!unchanged || gbb_test_copy_instance_bytes(machine, bytes, size) != GBB_OK) {
        fprintf(stderr, "state snapshot seam violated its caller-buffer contract\n");
        free(bytes);
        gbb_destroy(machine);
        return 1;
    }
    free(bytes);
    gbb_destroy(machine);
    puts("state-fuzz-control pass bounded_snapshot=null_and_capacity_refusals");
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "state_fuzz_mutant") == 0) {
        const uint8_t seed[] = {FUZZ_STATE_TAG, 0u, 1u, 0u, 0u, 0u, 0u};
        return gbb_fuzz_core_one_input(seed, sizeof(seed));
    }
    if (argc == 2 && strcmp(argv[1], "state_control") == 0) {
        const uint8_t seed[] = {FUZZ_STATE_TAG, 0u, 7u, 0u, 0u, 0u, 0u};
        if (gbb_fuzz_core_one_input(seed, sizeof(seed)) != 0 ||
            (last_state_observation.witness &
             (FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE | FUZZ_STATE_WITNESS_TARGET)) !=
                (FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE | FUZZ_STATE_WITNESS_TARGET)) {
            fprintf(stderr, "state fuzz unrelated accepted-state control failed\n");
            return 1;
        }
        puts("state-fuzz-control pass unrelated=accepted-state-closure");
        return 0;
    }
    if (argc != 1) {
        fprintf(stderr, "unknown state fuzz control mode\n");
        return 2;
    }
    if (run_state_fuzz_snapshot_api_controls() != 0) return 1;
    static const struct {
        uint8_t profile;
        uint8_t scenario;
        uint8_t payload[4];
        uint32_t expected_witness;
        const char *name;
    } cases[] = {
        {1u, 0u, {0u, 0u, 0u, 0u}, FUZZ_STATE_WITNESS_HEADER_ONLY, "header-only control"},
        {0u, 1u, {0u, 0u, 0u, 0u}, FUZZ_STATE_WITNESS_LATE_INVALID | FUZZ_STATE_WITNESS_NO_WRITE,
         "late invalid field"},
        {0u, 2u, {0xFFu, 0u, 0u, 0u}, FUZZ_STATE_WITNESS_PREMATURE_APPLY | FUZZ_STATE_WITNESS_NO_WRITE,
         "premature-apply refusal"},
        {2u, 3u, {0u, 0u, 0u, 0u}, FUZZ_STATE_WITNESS_CAP_SENTINEL | FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE,
         "cap and timer sentinel"},
        {1u, 4u, {0x81u, 0u, 0u, 0u}, FUZZ_STATE_WITNESS_SIGNED_AUDIO | FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE,
         "signed audio edge"},
        {2u, 5u, {4u, 4u, 0u, 0u}, FUZZ_STATE_WITNESS_QUEUE_ORDER | FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE,
         "equal-time queue ordering"},
        {2u, 6u, {59u, 58u, 23u, 0xFFu}, FUZZ_STATE_WITNESS_RTC_PALETTE | FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE,
         "RTC and palette"},
        {0u, 7u, {0u, 0u, 0u, 0u}, FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE,
         "accepted load and closure"},
    };
    const uint32_t required = FUZZ_STATE_WITNESS_HEADER_ONLY | FUZZ_STATE_WITNESS_LATE_INVALID |
        FUZZ_STATE_WITNESS_PREMATURE_APPLY | FUZZ_STATE_WITNESS_NO_WRITE |
        FUZZ_STATE_WITNESS_CAP_SENTINEL | FUZZ_STATE_WITNESS_SIGNED_AUDIO |
        FUZZ_STATE_WITNESS_QUEUE_ORDER | FUZZ_STATE_WITNESS_RTC_PALETTE |
        FUZZ_STATE_WITNESS_ACCEPTED_CLOSURE | FUZZ_STATE_WITNESS_TARGET;
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        const uint8_t seed[] = {FUZZ_STATE_TAG, cases[i].profile, cases[i].scenario,
                                cases[i].payload[0], cases[i].payload[1],
                                cases[i].payload[2], cases[i].payload[3]};
        const int failures_before = gbb_fuzz_core_contract_failures();
        if (gbb_fuzz_core_one_input(seed, sizeof(seed)) != 0) {
            fprintf(stderr, "state fuzz seed failed: %s\n", cases[i].name);
            return 1;
        }
        int selected = 0;
        uint8_t profile = 0u, scenario = 0u;
        unsigned operations = 0u;
        uint32_t witness = 0u;
        gbb_fuzz_core_state_observation(&selected, &profile, &scenario, &operations,
                                        &witness, NULL);
        const uint8_t expected_profile = cases[i].scenario == 6u ? 2u : cases[i].profile;
        if (gbb_fuzz_core_contract_failures() != failures_before || !selected ||
            profile != expected_profile || scenario != cases[i].scenario ||
            operations == 0u || operations > FUZZ_STATE_OPERATION_LIMIT ||
            (witness & (cases[i].expected_witness | FUZZ_STATE_WITNESS_TARGET)) !=
                (cases[i].expected_witness | FUZZ_STATE_WITNESS_TARGET)) {
            fprintf(stderr, "state fuzz witness failed: %s selected=%d profile=%u scenario=%u "
                            "operations=%u witness=0x%X\n", cases[i].name, selected,
                    profile, scenario, operations, witness);
            return 1;
        }
    }
    int selected = 1;
    uint32_t seen = 0u;
    gbb_fuzz_core_state_observation(&selected, NULL, NULL, NULL, NULL, &seen);
    if (selected != 1 || (seen & required) != required) {
        fprintf(stderr, "state fuzz aggregate witness missing: selected=%d seen=0x%X\n",
                selected, seen);
        return 1;
    }
    printf("state-load-fuzz pass entrypoint=gbb_fuzz_state_one_input semantic_witnesses=9 "
           "refusal_controls=3 accepted_closures=5 operations_per_input<=16\n");
    return 0;
}
#endif
