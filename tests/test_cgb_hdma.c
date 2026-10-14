/* Public guest-level CGB HDMA scheduler regressions (Phase 13, D-08/D-10/D-14).
 * Every oracle below is produced by an inline guest through the public API. */
#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ROM_SIZE 32768u
#define HALT_WAKE_BUDGET 60000u
#define GUEST_BUDGET 100000u
#define FIXTURE_BUDGET 1404480u
#define FIXTURE_FRAME_WIDTH 160u
#define FIXTURE_FRAME_HEIGHT 144u
#define MAX_FIXUPS 16u

typedef struct {
    uint8_t bytes[2048];
    size_t size;
    size_t labels[8];
    uint8_t label_set[8];
    struct { size_t operand; uint8_t label; uint8_t opcode; } fixups[MAX_FIXUPS];
    size_t fixup_count;
    int failed;
} guest_program;

enum { LABEL_MODE3 = 0, LABEL_FIRST_BLOCK, LABEL_COMPLETE, LABEL_COPY_1, LABEL_COPY_2 };

static void emit(guest_program *p, uint8_t byte) {
    if (p->failed || p->size >= sizeof(p->bytes)) { p->failed = 1; return; }
    p->bytes[p->size++] = byte;
}
static void label(guest_program *p, unsigned id) {
    if (p->failed || id >= sizeof(p->labels) / sizeof(p->labels[0])) { p->failed = 1; return; }
    p->labels[id] = p->size;
    p->label_set[id] = 1u;
}
static void branch(guest_program *p, uint8_t opcode, unsigned id) {
    if (id >= sizeof(p->labels) / sizeof(p->labels[0]) || p->fixup_count >= MAX_FIXUPS) {
        p->failed = 1; return;
    }
    emit(p, opcode);
    const size_t operand = p->size;
    emit(p, 0u);
    if (p->failed) return;
    p->fixups[p->fixup_count].operand = operand;
    p->fixups[p->fixup_count].label = (uint8_t)id;
    p->fixups[p->fixup_count].opcode = opcode;
    ++p->fixup_count;
}
static int resolve(guest_program *p) {
    if (p->failed || p->fixup_count > MAX_FIXUPS) return 0;
    for (size_t i = 0u; i < p->fixup_count; ++i) {
        const uint8_t id = p->fixups[i].label;
        if (id >= 8u || !p->label_set[id]) return 0;
        const long offset = (long)p->labels[id] - (long)(p->fixups[i].operand + 1u);
        if (offset < -128L || offset > 127L) return 0;
        p->bytes[p->fixups[i].operand] = (uint8_t)(int8_t)offset;
    }
    return 1;
}
static void ld_a(guest_program *p, uint8_t value) { emit(p, 0x3Eu); emit(p, value); }
static void write_io(guest_program *p, uint8_t address, uint8_t value) {
    ld_a(p, value); emit(p, 0xE0u); emit(p, address);
}
static void write_abs(guest_program *p, uint16_t address, uint8_t value) {
    ld_a(p, value); emit(p, 0xEAu); emit(p, (uint8_t)address); emit(p, (uint8_t)(address >> 8));
}
static void store_a_abs(guest_program *p, uint16_t address) {
    emit(p, 0xEAu); emit(p, (uint8_t)address); emit(p, (uint8_t)(address >> 8));
}
static void copy_vram_to_wram(guest_program *p, uint16_t source,
                              uint16_t destination, uint8_t count, unsigned loop_label) {
    emit(p, 0x21u); emit(p, (uint8_t)source); emit(p, (uint8_t)(source >> 8));
    emit(p, 0x11u); emit(p, (uint8_t)destination); emit(p, (uint8_t)(destination >> 8));
    ld_a(p, count); emit(p, 0x47u); /* LD B,count */
    label(p, loop_label);
    emit(p, 0x2Au); /* LD A,(HL+) */
    emit(p, 0x12u); /* LD (DE),A */
    emit(p, 0x13u); /* INC DE */
    emit(p, 0x05u); /* DEC B */
    branch(p, 0x20u, loop_label);
}
static uint8_t source_pattern(unsigned index) { return (uint8_t)(index * 37u + 11u); }

static void fix_header_checksum(uint8_t *rom) {
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

static int build_rom(uint8_t rom[ROM_SIZE], const guest_program *program,
                     const uint8_t *timer_vector, size_t vector_size,
                     unsigned source_pattern_bytes) {
    if (program->failed || program->size > ROM_SIZE - 0x150u ||
        vector_size > 0x100u - 0x50u || source_pattern_bytes > ROM_SIZE - 0x200u ||
        (timer_vector == NULL && vector_size != 0u)) return 0;
    memset(rom, 0, ROM_SIZE);
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = 0x80u;
    memcpy(rom + 0x150u, program->bytes, program->size);
    if (timer_vector != NULL) memcpy(rom + 0x50u, timer_vector, vector_size);
    for (unsigned i = 0u; i < source_pattern_bytes; ++i)
        rom[0x200u + i] = source_pattern(i);
    fix_header_checksum(rom);
    return 1;
}

static int load_machine(const uint8_t *rom, size_t size, gbb_instance **out) {
    *out = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, out) != GBB_OK) return 0;
    if (gbb_load_rom(*out, rom, size) == GBB_OK) return 1;
    gbb_destroy(*out); *out = NULL;
    return 0;
}

static gbb_run_result run_public(gbb_instance *machine, uint64_t budget, int use_run_ex) {
    return use_run_ex ? gbb_run_ex(machine, budget, NULL, 0u, NULL, 0u)
                      : gbb_run(machine, budget, NULL, 0u);
}

static int build_halt_wake_rom(uint8_t rom[ROM_SIZE], int enable_ime) {
    static const uint8_t timer_vector[] = {
        0xF0,0x55,0xEA,0x00,0xC1, /* store FF55 at wake */
        0x3E,0x5A,0xEA,0x01,0xC1, /* mark real timer-vector dispatch */
        0xAF,0xE0,0x07,0xD9       /* stop timer and RETI */
    };
    guest_program p = {0};
    write_io(&p, 0x51u, 0x02u); /* FF51 = $0200 */
    write_io(&p, 0x52u, 0x00u);
    write_io(&p, 0x53u, 0x00u);
    write_io(&p, 0x54u, 0x00u);
    write_io(&p, 0x55u, 0x82u); /* three HBlank blocks */
    write_abs(&p, 0xFFFFu, 0x04u); /* IE = timer */
    emit(&p, 0xAFu); emit(&p, 0xE0u); emit(&p, 0x0Fu); /* clear IF */
    emit(&p, 0xAFu); emit(&p, 0xE0u); emit(&p, 0x05u); /* TIMA = 0 */
    emit(&p, 0xAFu); emit(&p, 0xE0u); emit(&p, 0x06u); /* TMA = 0 */
    write_io(&p, 0x07u, 0x05u); /* timer on, 16 T period */
    if (enable_ime) {
        emit(&p, 0xFBu); emit(&p, 0x00u); /* EI; retire before HALT */
        emit(&p, 0x76u);
    } else {
        emit(&p, 0x00u); emit(&p, 0x76u); /* IME remains off */
        emit(&p, 0xF0u); emit(&p, 0x55u); store_a_abs(&p, 0xC100u);
        emit(&p, 0xAFu); emit(&p, 0xE0u); emit(&p, 0x07u); /* stop timer after wake */
    }
    label(&p, LABEL_COMPLETE);
    emit(&p, 0xF0u); emit(&p, 0x55u); emit(&p, 0xFEu); emit(&p, 0xFFu);
    branch(&p, 0x20u, LABEL_COMPLETE);
    emit(&p, 0xF0u); emit(&p, 0x55u); store_a_abs(&p, 0xC102u); /* guest completion readback */
    write_io(&p, 0x40u, 0x00u); /* unlock VRAM reads after the transfer */
    copy_vram_to_wram(&p, 0x8000u, 0xC200u, 48u, LABEL_COPY_1);
    write_abs(&p, 0xC103u, 0xA5u);
    emit(&p, 0x76u);
    return resolve(&p) && build_rom(rom, &p, timer_vector, sizeof(timer_vector), 48u);
}

static int run_halt_wake(int enable_ime, int use_run_ex) {
    uint8_t rom[ROM_SIZE];
    if (!build_halt_wake_rom(rom, enable_ime)) return 1;
    gbb_instance *machine = NULL;
    if (!load_machine(rom, sizeof(rom), &machine)) return 1;
    unsigned calls = 0u;
    while (gbb_peek_ram(machine, 0xC103u) != 0xA5u && calls++ < 4u) {
        const gbb_run_result run = run_public(machine, HALT_WAKE_BUDGET, use_run_ex);
        if (run.consumed_half_dots == 0u ||
            run.reason == GBB_STOP_UNSUPPORTED_BUS || run.reason == GBB_STOP_LOCKUP ||
            run.reason == GBB_STOP_INVALID_STATE) {
            fprintf(stderr, "guest halt: run consumed=%llu reason=%d\n",
                    (unsigned long long)run.consumed_half_dots,
                    (int)run.reason);
            gbb_destroy(machine);
            return 1;
        }
    }
    const uint8_t status_at_wake = gbb_peek_ram(machine, 0xC100u);
    const uint8_t dispatched = gbb_peek_ram(machine, 0xC101u);
    if (status_at_wake != 0x02u) {
        fprintf(stderr, "guest halt: wake FF55 expected=02 actual=%02X\n", status_at_wake);
        gbb_destroy(machine); return 1;
    }
    if (dispatched != (enable_ime ? 0x5Au : 0u)) {
        fprintf(stderr, "guest halt: timer vector marker expected=%02X actual=%02X\n",
                enable_ime ? 0x5Au : 0u, dispatched);
        gbb_destroy(machine); return 1;
    }
    if (gbb_peek_ram(machine, 0xC102u) != 0xFFu) {
        fprintf(stderr, "guest halt: completion FF55 expected=FF actual=%02X\n",
                gbb_peek_ram(machine, 0xC102u));
        gbb_destroy(machine); return 1;
    }
    for (unsigned i = 0u; i < 48u; ++i) {
        const uint8_t actual = gbb_peek_ram(machine, (uint16_t)(0xC200u + i));
        const uint8_t expected = source_pattern(i);
        if (actual != expected) {
            fprintf(stderr, "guest halt: readback[%u] expected=%02X actual=%02X\n",
                    i, expected, actual);
            gbb_destroy(machine); return 1;
        }
    }
    gbb_destroy(machine);
    return 0;
}

static int build_steal_rom(uint8_t rom[ROM_SIZE], int double_speed) {
    guest_program p = {0};
    if (double_speed) {
        write_io(&p, 0x4Du, 0x01u);
        emit(&p, 0x10u); emit(&p, 0x00u); /* STOP switches to double speed */
    }
    write_io(&p, 0x40u, 0x00u); /* reset guest-visible PPU phase */
    write_io(&p, 0x40u, 0x91u);
    write_io(&p, 0x51u, 0x02u); /* source $0200 */
    write_io(&p, 0x52u, 0x00u);
    write_io(&p, 0x53u, 0x00u); /* destination $8000 */
    write_io(&p, 0x54u, 0x00u);
    label(&p, LABEL_MODE3);
    emit(&p, 0xF0u); emit(&p, 0x41u); /* STAT */
    store_a_abs(&p, 0xC103u); /* preserve the raw mode observed by the guest */
    emit(&p, 0xE6u); emit(&p, 0x03u);
    emit(&p, 0xFEu); emit(&p, 0x03u);
    branch(&p, 0x20u, LABEL_MODE3);
    write_io(&p, 0x55u, 0x7Fu); /* 128-block GDMA, also a long CPU-steal window */
    emit(&p, 0xF0u); emit(&p, 0x44u); store_a_abs(&p, 0xC100u); /* LY after the start */
    label(&p, LABEL_COMPLETE);
    emit(&p, 0xF0u); emit(&p, 0x55u); emit(&p, 0xFEu); emit(&p, 0xFFu);
    branch(&p, 0x20u, LABEL_COMPLETE);
    write_io(&p, 0x40u, 0x00u); /* make final VRAM reads unlocked */
    emit(&p, 0xFAu); emit(&p, 0x00u); emit(&p, 0x80u); store_a_abs(&p, 0xC101u);
    emit(&p, 0xFAu); emit(&p, 0xFFu); emit(&p, 0x87u); store_a_abs(&p, 0xC102u);
    write_abs(&p, 0xC104u, 0xA5u);
    emit(&p, 0x76u);
    return resolve(&p) && build_rom(rom, &p, NULL, 0u, 2048u);
}

static int run_steal_guest(int double_speed, int check_timing, int use_run_ex) {
    uint8_t rom[ROM_SIZE];
    if (!build_steal_rom(rom, double_speed)) return 1;
    gbb_instance *machine = NULL;
    if (!load_machine(rom, sizeof(rom), &machine)) return 1;
    for (unsigned call = 0u; call < 4u && gbb_peek_ram(machine, 0xC104u) != 0xA5u; ++call) {
        const gbb_run_result run = run_public(machine, GUEST_BUDGET, use_run_ex);
        if (run.reason == GBB_STOP_UNSUPPORTED_BUS || run.reason == GBB_STOP_LOCKUP ||
            run.reason == GBB_STOP_INVALID_STATE || run.consumed_half_dots == 0u) {
            fprintf(stderr, "guest steal: invalid run reason=%d consumed=%llu\n", (int)run.reason,
                    (unsigned long long)run.consumed_half_dots);
            gbb_destroy(machine); return 1;
        }
    }
    if (gbb_peek_ram(machine, 0xC104u) != 0xA5u) {
        fprintf(stderr, "guest steal: guest did not finish within bounded run calls\n");
        gbb_destroy(machine); return 1;
    }
    const uint8_t mode = gbb_peek_ram(machine, 0xC103u);
    const uint8_t first = gbb_peek_ram(machine, 0xC101u);
    const uint8_t last = gbb_peek_ram(machine, 0xC102u);
    if ((mode & 0x03u) != 0x03u) {
        fprintf(stderr, "guest steal: GDMA was not armed in mode 3 (mode=%02X)\n", mode);
        gbb_destroy(machine); return 1;
    }
    if (first != source_pattern(0u) || last != source_pattern(2047u)) {
        fprintf(stderr, "guest steal: GDMA data expected=%02X/%02X actual=%02X/%02X\n",
                source_pattern(0u), source_pattern(2047u), first, last);
        gbb_destroy(machine); return 1;
    }
    if (check_timing && gbb_peek_ram(machine, 0xC100u) < 8u) {
        fprintf(stderr, "guest steal: CPU timing predicate expected LY>=8 during GDMA, actual=%02X\n",
                gbb_peek_ram(machine, 0xC100u));
        gbb_destroy(machine); return 1;
    }
    gbb_destroy(machine);
    return 0;
}

static int run_halt_bug_guest(void) {
    static const uint8_t program[] = {
        0x3E,0x01,0xEA,0xFF,0xFF,0xE0,0x0F, /* pending enabled VBlank with IME off */
        0x76,0x06,0x99,                     /* HALT bug duplicates LD B opcode as its operand */
        0x78,0xEA,0x20,0xC0,0x76
    };
    guest_program p = {0};
    memcpy(p.bytes, program, sizeof(program)); p.size = sizeof(program);
    uint8_t rom[ROM_SIZE]; if (!build_rom(rom, &p, NULL, 0u, 0u)) return 1;
    gbb_instance *machine = NULL;
    if (!load_machine(rom, sizeof(rom), &machine)) return 1;
    const gbb_run_result run = gbb_run(machine, 256u, NULL, 0u);
    const uint8_t actual = gbb_peek_ram(machine, 0xC020u);
    gbb_destroy(machine);
    if (run.consumed_half_dots == 0u || actual != 0x06u) {
        fprintf(stderr, "guest controls: pending-IRQ HALT bug marker expected=06 actual=%02X\n", actual);
        return 1;
    }
    return 0;
}

static int build_banks_rom(uint8_t rom[ROM_SIZE]) {
    guest_program p = {0};
    write_io(&p, 0x70u, 0x01u); /* populate physical WRAM bank 1 */
    for (unsigned i = 0u; i < 16u; ++i) write_abs(&p, (uint16_t)(0xD000u + i), (uint8_t)(0xA0u + i));
    write_io(&p, 0x70u, 0x02u); /* populate physical WRAM bank 2 */
    for (unsigned i = 0u; i < 16u; ++i) write_abs(&p, (uint16_t)(0xD010u + i), (uint8_t)(0xC0u + i));
    write_io(&p, 0x70u, 0x01u);
    write_io(&p, 0x4Fu, 0x00u);
    write_io(&p, 0x51u, 0xD0u); write_io(&p, 0x52u, 0x00u);
    write_io(&p, 0x53u, 0x00u); write_io(&p, 0x54u, 0x00u);
    write_io(&p, 0x55u, 0x81u); /* two HBlank blocks */
    label(&p, LABEL_FIRST_BLOCK);
    emit(&p, 0xF0u); emit(&p, 0x55u); emit(&p, 0xFEu); emit(&p, 0x01u);
    branch(&p, 0x28u, LABEL_FIRST_BLOCK); /* wait until one block remains */
    write_io(&p, 0x4Fu, 0x01u); /* next block samples VRAM bank 1 */
    write_io(&p, 0x70u, 0x02u); /* next block reads physical WRAM bank 2 */
    label(&p, LABEL_COMPLETE);
    emit(&p, 0xF0u); emit(&p, 0x55u); emit(&p, 0xFEu); emit(&p, 0xFFu);
    branch(&p, 0x20u, LABEL_COMPLETE);
    write_io(&p, 0x40u, 0x00u); /* unlock VRAM reads */
    write_io(&p, 0x4Fu, 0x00u);
    copy_vram_to_wram(&p, 0x8000u, 0xC100u, 16u, LABEL_COPY_1);
    write_io(&p, 0x4Fu, 0x01u);
    copy_vram_to_wram(&p, 0x8010u, 0xC110u, 16u, LABEL_COPY_2);
    emit(&p, 0xF0u); emit(&p, 0x55u); store_a_abs(&p, 0xC120u);
    emit(&p, 0x76u);
    return resolve(&p) && build_rom(rom, &p, NULL, 0u, 0u);
}

static int run_banks_guest(void) {
    uint8_t rom[ROM_SIZE]; if (!build_banks_rom(rom)) return 1;
    gbb_instance *machine = NULL;
    if (!load_machine(rom, sizeof(rom), &machine)) return 1;
    const gbb_run_result run = gbb_run(machine, GUEST_BUDGET, NULL, 0u);
    if (run.reason == GBB_STOP_UNSUPPORTED_BUS || run.reason == GBB_STOP_LOCKUP ||
        run.reason == GBB_STOP_INVALID_STATE) {
        fprintf(stderr, "guest banks: run stopped reason=%d\n", (int)run.reason);
        gbb_destroy(machine); return 1;
    }
    if (gbb_peek_ram(machine, 0xC120u) != 0xFFu) {
        fprintf(stderr, "guest banks: FF55 completion readback expected=FF actual=%02X\n",
                gbb_peek_ram(machine, 0xC120u));
        gbb_destroy(machine); return 1;
    }
    for (unsigned i = 0u; i < 16u; ++i) {
        const uint8_t first = gbb_peek_ram(machine, (uint16_t)(0xC100u + i));
        const uint8_t second = gbb_peek_ram(machine, (uint16_t)(0xC110u + i));
        if (first != (uint8_t)(0xA0u + i) || second != (uint8_t)(0xC0u + i)) {
            fprintf(stderr, "guest banks: byte %u expected=%02X/%02X actual=%02X/%02X\n",
                    i, (uint8_t)(0xA0u + i), (uint8_t)(0xC0u + i), first, second);
            gbb_destroy(machine); return 1;
        }
    }
    gbb_destroy(machine);
    return 0;
}

static int read_fixture(const char *path, uint8_t **out_rom, size_t *out_size) {
    *out_rom = NULL;
    *out_size = 0u;
    FILE *file = fopen(path, "rb");
    if (file == NULL || fseek(file, 0, SEEK_END) != 0) {
        if (file != NULL) fclose(file);
        fprintf(stderr, "fixture: cannot open ROM\n"); return 0;
    }
    const long length = ftell(file);
    if (length != (long)ROM_SIZE || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file); fprintf(stderr, "fixture: ROM size is not exactly 32 KiB\n"); return 0;
    }
    uint8_t *rom = (uint8_t *)malloc(ROM_SIZE);
    if (rom == NULL || fread(rom, 1u, ROM_SIZE, file) != ROM_SIZE) {
        free(rom); fclose(file); fprintf(stderr, "fixture: bounded ROM read failed\n"); return 0;
    }
    fclose(file);
    *out_rom = rom;
    *out_size = ROM_SIZE;
    return 1;
}

static int disable_fixture_transfer(uint8_t *rom, size_t size) {
    size_t found = 0u;
    size_t offset = 0u;
    if (size != ROM_SIZE) return 0;
    for (size_t i = 0u; i + 1u < size; ++i) {
        if (rom[i] == 0xE0u && rom[i + 1u] == 0x55u) {
            offset = i;
            ++found;
        }
    }
    if (found != 1u) {
        fprintf(stderr, "control: FF55 start signature count=%zu, expected=1\n", found);
        return 0;
    }
    rom[offset] = 0x00u;
    rom[offset + 1u] = 0x00u;
    return 1;
}

static int run_fixture_image(const uint8_t *rom, size_t size, int expect_pass,
                             uint8_t *out_marker, uint8_t *out_initial_status) {
    gbb_instance *machine = NULL;
    if (!load_machine(rom, size, &machine)) {
        fprintf(stderr, "fixture: public ROM loader rejected image\n"); return 0;
    }
    static const uint64_t partitions[] = {997u, 8191u, 4093u, 16384u, 6553u};
    uint64_t total = 0u;
    size_t partition = 0u;
    while (total < FIXTURE_BUDGET) {
        const uint64_t remaining = FIXTURE_BUDGET - total;
        uint64_t budget = partitions[partition % (sizeof(partitions) / sizeof(partitions[0]))];
        if (remaining < 256u) budget = 256u;
        else if (budget > remaining) budget = remaining;
        const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
        if (run.reason != GBB_STOP_BUDGET || run.consumed_half_dots == 0u ||
            run.consumed_half_dots > budget || run.consumed_half_dots > remaining + 255u) {
            fprintf(stderr, "fixture: bounded run stopped reason=%d consumed=%llu budget=%llu remaining=%llu\n",
                    (int)run.reason, (unsigned long long)run.consumed_half_dots,
                    (unsigned long long)budget, (unsigned long long)remaining);
            gbb_destroy(machine); return 0;
        }
        total += run.consumed_half_dots;
        ++partition;
    }
    const uint8_t marker = gbb_peek_ram(machine, 0xC000u);
    const uint8_t initial_status = gbb_peek_ram(machine, 0xC001u);
    const uint8_t first_block_status = gbb_peek_ram(machine, 0xC002u);
    const uint8_t completed_status = gbb_peek_ram(machine, 0xC003u);
    if (out_marker != NULL) *out_marker = marker;
    if (out_initial_status != NULL) *out_initial_status = initial_status;
    if (marker != (expect_pass ? 0xA5u : 0xEEu)) {
        fprintf(stderr, "fixture guest marker expected=%02X actual=%02X\n",
                expect_pass ? 0xA5u : 0xEEu, marker);
        gbb_destroy(machine); return 0;
    }
    if (expect_pass && (initial_status != 0x01u || first_block_status != 0x00u ||
                        completed_status != 0xFFu)) {
        fprintf(stderr, "fixture guest FF55 status expected=01/00/FF actual=%02X/%02X/%02X\n",
                initial_status, first_block_status, completed_status);
        gbb_destroy(machine); return 0;
    }
    if (!expect_pass && initial_status != 0xFFu) {
        fprintf(stderr, "control guest FF55 status expected=FF actual=%02X\n", initial_status);
        gbb_destroy(machine); return 0;
    }

    uint16_t pixels[FIXTURE_FRAME_WIDTH * FIXTURE_FRAME_HEIGHT];
    gbb_frame_info info;
    const gbb_error copied = gbb_copy_frame_rgb555(machine, pixels, sizeof(pixels),
                                                   FIXTURE_FRAME_WIDTH * sizeof(uint16_t), &info);
    if (copied != GBB_OK || info.generation == 0u || info.width != FIXTURE_FRAME_WIDTH ||
        info.height != FIXTURE_FRAME_HEIGHT) {
        fprintf(stderr, "fixture pixel predicate: completed RGB555 frame unavailable (error=%d)\n",
                (int)copied);
        gbb_destroy(machine); return 0;
    }
    const uint16_t left = expect_pass ? 0x001Fu : 0x7FFFu;
    const uint16_t right = expect_pass ? 0x7C00u : 0x7FFFu;
    for (unsigned y = 0u; y < FIXTURE_FRAME_HEIGHT; ++y) {
        for (unsigned x = 0u; x < FIXTURE_FRAME_WIDTH; ++x) {
            const uint16_t expected = expect_pass && x >= 80u ? right : left;
            const uint16_t actual = pixels[y * FIXTURE_FRAME_WIDTH + x];
            if (actual != expected) {
                fprintf(stderr, "fixture pixel predicate expected=%04X actual=%04X at (%u,%u)\n",
                        expected, actual, x, y);
                gbb_destroy(machine); return 0;
            }
        }
    }
    printf("fixture guest=%s marker=%02X ff55=%02X/%02X/%02X pixel_predicate=pass generation=%llu\n",
           expect_pass ? "pass" : "fail", marker, initial_status,
           first_block_status, completed_status, (unsigned long long)info.generation);
    gbb_destroy(machine);
    return 1;
}

static int run_fixture(const char *path, int check_controls) {
    uint8_t *rom = NULL;
    size_t size = 0u;
    if (!read_fixture(path, &rom, &size)) return 1;
    if (!run_fixture_image(rom, size, 1, NULL, NULL)) { free(rom); return 1; }
    if (check_controls) {
        uint8_t *disabled = (uint8_t *)malloc(size);
        if (disabled == NULL) { free(rom); fprintf(stderr, "control: bounded ROM copy allocation failed\n"); return 1; }
        memcpy(disabled, rom, size);
        if (!disable_fixture_transfer(disabled, size) ||
            !run_fixture_image(disabled, size, 0, NULL, NULL)) {
            free(disabled); free(rom); return 1;
        }
        free(disabled);
        puts("fixture control=disabled-transfer guest=fail pixel_predicate=pass");
    }
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "--fixture") == 0) return run_fixture(argv[2], 0);
    if (argc == 4 && strcmp(argv[1], "--fixture") == 0 &&
        strcmp(argv[3], "--check-controls") == 0) return run_fixture(argv[2], 1);
    if (argc == 2 && strcmp(argv[1], "guest_halt") == 0) {
        if (run_halt_wake(1, 0) == 0 && run_halt_wake(1, 1) == 0) {
            puts("cgb-hdma guest_halt pass"); return 0;
        }
        return 1;
    }
    if (argc == 2 && strcmp(argv[1], "guest_controls") == 0) {
        if (run_halt_wake(0, 1) == 0 && run_halt_bug_guest() == 0) {
            puts("cgb-hdma guest_controls pass"); return 0;
        }
        return 1;
    }
    if (argc == 2 && strcmp(argv[1], "guest_steal") == 0) {
        if (run_steal_guest(0, 1, 0) == 0 && run_steal_guest(1, 1, 1) == 0) {
            puts("cgb-hdma guest_steal pass"); return 0;
        }
        return 1;
    }
    if (argc == 2 && strcmp(argv[1], "guest_steal_data") == 0)
        return run_steal_guest(0, 0, 0);
    if (argc == 2 && strcmp(argv[1], "guest_banks") == 0) {
        if (run_banks_guest() == 0) { puts("cgb-hdma guest_banks pass"); return 0; }
        return 1;
    }
    fprintf(stderr, "usage: test_cgb_hdma <guest_halt|guest_controls|guest_steal|guest_steal_data|guest_banks|--fixture ROM [--check-controls]>\n");
    return 2;
}
