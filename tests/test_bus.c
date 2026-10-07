#include "gabbaboy/gabbaboy.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("ok 1 - %s\n", name); } while (0)

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;
extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);
extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);

static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}

static gbb_instance *load_program(const uint8_t *program, size_t length) {
    uint8_t *rom = calloc(1, 32768);
    if (rom == NULL) return NULL;
    memcpy(rom + 0x100, program, length);
    /* E7 plus the 25 header bytes' decrements wraps the checksum to zero. */
    rom[0x134] = 0xe7;
    fix_checksum(rom);
    assert(rom[0x14d] == 0);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static int reject_atomically(gbb_instance *m) {
    gbb_trace_record before, after, trace[2], untouched_trace[2];
    gbb_diagnostic_record diagnostics[32], untouched_diagnostics[32];
    uint8_t ram[8192], hram[127];
    gbb_test_bus_event events[8];
    memset(trace, 0xa5, sizeof(trace));
    memcpy(untouched_trace, trace, sizeof(trace));
    memset(diagnostics, 0x5a, sizeof(diagnostics));
    memcpy(untouched_diagnostics, diagnostics, sizeof(diagnostics));
    for (unsigned i = 0; i < sizeof(ram); ++i) ram[i] = gbb_peek_ram(m, (uint16_t)(0xc000u + i));
    for (unsigned i = 0; i < sizeof(hram); ++i) hram[i] = gbb_peek_ram(m, (uint16_t)(0xff80u + i));
    gbb_test_observer_set(m, events, 8);
    gbb_test_cpu_snapshot(m, &before);
    for (unsigned attempt = 0; attempt < 2; ++attempt) {
        gbb_run_result r = gbb_run_ex(m, 64, trace, 2, diagnostics, 32);
        REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS);
        REQUIRE(r.consumed_half_dots == 0 && r.trace_count == 0 && r.diagnostic_count == 0);
        REQUIRE(gbb_test_observer_count(m) == 0);
        REQUIRE(memcmp(trace, untouched_trace, sizeof(trace)) == 0);
        REQUIRE(memcmp(diagnostics, untouched_diagnostics, sizeof(diagnostics)) == 0);
        gbb_test_cpu_snapshot(m, &after);
        REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
        for (unsigned i = 0; i < sizeof(ram); ++i) REQUIRE(ram[i] == gbb_peek_ram(m, (uint16_t)(0xc000u + i)));
        for (unsigned i = 0; i < sizeof(hram); ++i) REQUIRE(hram[i] == gbb_peek_ram(m, (uint16_t)(0xff80u + i)));
    }
    return 0;
}

static int unsupported_reads(void) {
    /* Each operand family must reject before a timed read, flag change or HL update. */
    static const uint8_t hl_reads[] = {0x46,0x4e,0x56,0x5e,0x66,0x6e,0x7e,
        0x86,0x8e,0x96,0x9e,0xa6,0xae,0xb6,0xbe,0x34,0x35,0x2a,0x3a};
    static const uint16_t absent[] = {0xa000,0xff03,0xff08,0xff7f};
    for (size_t a = 0; a < sizeof(absent) / sizeof(absent[0]); ++a) {
        for (size_t i = 0; i < sizeof(hl_reads); ++i) {
            const uint8_t p[] = {0x21,(uint8_t)absent[a],(uint8_t)(absent[a] >> 8),hl_reads[i]};
            gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
            REQUIRE(gbb_run(m, 24, NULL, 0).consumed_half_dots == 24);
            REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
        }
        /* CB rotates, BIT, RES and SET all read (HL), including writeback families. */
        for (unsigned op = 6; op < 256; op += 8) {
            const uint8_t p[] = {0x21,(uint8_t)absent[a],(uint8_t)(absent[a] >> 8),0xcb,(uint8_t)op};
            gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
            REQUIRE(gbb_run(m, 24, NULL, 0).consumed_half_dots == 24);
            REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
        }
        for (unsigned pair = 0; pair < 2; ++pair) {
            const uint8_t p[] = {(uint8_t)(pair == 0 ? 0x01 : 0x11),(uint8_t)absent[a],
                (uint8_t)(absent[a] >> 8),(uint8_t)(pair == 0 ? 0x0a : 0x1a)};
            gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
            REQUIRE(gbb_run(m, 24, NULL, 0).consumed_half_dots == 24);
            REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
        }
        const uint8_t p[] = {0xfa,(uint8_t)absent[a],(uint8_t)(absent[a] >> 8)};
        gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
        REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
    }
    static const uint8_t missing_io[] = {0x03,0x08,0x7f};
    for (size_t i = 0; i < sizeof(missing_io); ++i) {
        const uint8_t immediate[] = {0xf0,missing_io[i]};
        gbb_instance *m = load_program(immediate, sizeof(immediate)); REQUIRE(m != NULL);
        REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
        const uint8_t indexed[] = {0x0e,missing_io[i],0xf2};
        m = load_program(indexed, sizeof(indexed)); REQUIRE(m != NULL);
        REQUIRE(gbb_run(m, 16, NULL, 0).consumed_half_dots == 16);
        REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
    }
    return 0;
}

static int unsupported_stack(void) {
    /* FE9F is the last OAM byte; its second stack byte at FEA0 is unusable. */
    static const uint16_t addresses[] = {0xa000,0xfe9f,0xff02};
    static const uint8_t reads[] = {0xc1,0xd1,0xe1,0xf1,0xc9,0xd9,0xc8,0xd0};
    for (size_t a = 0; a < sizeof(addresses) / sizeof(addresses[0]); ++a) {
        for (size_t i = 0; i < sizeof(reads); ++i) {
            const uint8_t p[] = {0x31,(uint8_t)addresses[a],(uint8_t)(addresses[a] >> 8),reads[i]};
            gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
            REQUIRE(gbb_run(m, 24, NULL, 0).consumed_half_dots == 24);
            REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
        }
    }
    /* An untaken return performs no stack read, even with an absent stack. */
    const uint8_t p[] = {0x31,0x00,0xa0,0xc0,0xd8,0x00};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[4]; gbb_run_result r = gbb_run(m, 64, t, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 64 && r.trace_count == 4);
    REQUIRE(t[3].pc == 0x105 && t[3].sp == 0xa000);
    gbb_destroy(m);
    const uint8_t other_untaken[] = {0x31,0x00,0xa0,0xb7,0xc8,0x37,0xd0,0x00};
    m = load_program(other_untaken, sizeof(other_untaken)); REQUIRE(m != NULL);
    gbb_trace_record all[6]; r = gbb_run(m, 80, all, 6);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 80 && r.trace_count == 6);
    REQUIRE(all[5].pc == 0x107 && all[5].sp == 0xa000);
    gbb_destroy(m);
    const uint8_t taken_nz[] = {0x31,0x00,0xa0,0xb7,0xc0};
    m = load_program(taken_nz, sizeof(taken_nz)); REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, 32, NULL, 0).consumed_half_dots == 32);
    REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
    const uint8_t taken_c[] = {0x31,0x00,0xa0,0x37,0xd8};
    m = load_program(taken_c, sizeof(taken_c)); REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, 32, NULL, 0).consumed_half_dots == 32);
    REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
    return 0;
}

static int unsupported_fetch(void) {
    static const uint16_t pc[] = {0xa000,0xfea0,0xff03};
    static const uint8_t opcode[] = {0,0,0};
    for (size_t i = 0; i < sizeof(pc) / sizeof(pc[0]); ++i) {
        uint8_t rom[32768] = {0};
        rom[0x100] = 0xc3; rom[0x101] = (uint8_t)pc[i]; rom[0x102] = (uint8_t)(pc[i] >> 8);
        if (pc[i] < sizeof(rom)) rom[pc[i]] = opcode[i];
        fix_checksum(rom); gbb_instance *m = NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
        REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
        gbb_run_result initial = gbb_run(m, 32, NULL, 0);
        REQUIRE(initial.consumed_half_dots == 32);
        REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
    }
    /* The last OAM byte holds an immediate opcode whose operand lies in FEA0. */
    const uint8_t oam_operand[] = {0xaf,0xe0,0x40,0x21,0x9f,0xfe,0x3e,0x06,
                                  0x77,0xc3,0x9f,0xfe};
    gbb_instance *m = load_program(oam_operand, sizeof(oam_operand)); REQUIRE(m != NULL);
    gbb_run_result r = gbb_run(m, 192, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS && r.consumed_half_dots != 0);
    REQUIRE(reject_atomically(m) == 0); gbb_destroy(m);
    return 0;
}

static int halt_bug_fetch(void) {
    static const uint8_t opcodes[] = {0x06,0xcb,0x01};
    for (size_t i = 0; i < sizeof(opcodes); ++i) {
        uint16_t at = 0x0200;
        const uint8_t p[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0xc3,(uint8_t)(at-1u),(uint8_t)((at-1u)>>8)};
        uint8_t rom[32768] = {0}; memcpy(rom + 0x100, p, sizeof(p));
        rom[at-1u] = 0x76; rom[at] = opcodes[i];
        if (opcodes[i] == 0x01) rom[at + 1u] = 0x12;
        fix_checksum(rom); gbb_instance *m = NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
        REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
        REQUIRE(gbb_run(m, 120, NULL, 0).consumed_half_dots == 120);
        gbb_trace_record trace, snapshot; unsigned cost = opcodes[i] == 0x01 ? 24 : 16;
        gbb_run_result r = gbb_run(m, cost, &trace, 1);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == cost && r.trace_count == 1);
        REQUIRE(trace.pc == at && trace.opcode[0] == opcodes[i] && trace.opcode[1] == opcodes[i]);
        uint16_t next_pc = (uint16_t)(at + (opcodes[i] == 0x01 ? 2u : 1u));
        gbb_test_cpu_snapshot(m, &snapshot); REQUIRE(snapshot.pc == next_pc);
        if (opcodes[i] == 0x06) REQUIRE(snapshot.b == 0x06);
        if (opcodes[i] == 0x01) REQUIRE(snapshot.b == 0x12 && snapshot.c == 0x01);
        gbb_trace_record next;
        r = gbb_run(m, 8, &next, 1);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 8 && r.trace_count == 1);
        REQUIRE(next.pc == next_pc);
        gbb_destroy(m);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    printf("1..1\n");
    if (strcmp(argv[1], "unsupported_reads") == 0) { REQUIRE(unsupported_reads() == 0); PASS("bus_unsupported_reads"); return 0; }
    if (strcmp(argv[1], "unsupported_stack") == 0) { REQUIRE(unsupported_stack() == 0); PASS("bus_unsupported_stack"); return 0; }
    if (strcmp(argv[1], "unsupported_fetch") == 0) { REQUIRE(unsupported_fetch() == 0); PASS("bus_unsupported_fetch"); return 0; }
    if (strcmp(argv[1], "halt_bug_fetch") == 0) { REQUIRE(halt_bug_fetch() == 0); PASS("bus_halt_bug_fetch"); return 0; }
    if (strcmp(argv[1], "wram_guest") == 0) {
        const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x42,0x77,0x7E};
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_run_result r = gbb_run(m, 56, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 56);
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0x42);
        gbb_trace_record trace[8];
        r = gbb_run(m, 8, trace, 8);
        REQUIRE(r.consumed_half_dots == 0);
        gbb_destroy(m);
        PASS("bus_wram_guest");
        return 0;
    }
    if (strcmp(argv[1], "echo_hram") == 0) {
        const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x91,0x77,0x21,0x00,0xE0,0x7E};
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_run_result r = gbb_run(m, 80, NULL, 0);
        REQUIRE(r.consumed_half_dots == 80);
        REQUIRE(gbb_peek_ram(m, 0xE000) == 0x91);
        gbb_destroy(m);
        const uint8_t hram[] = {0x21,0x80,0xFF,0x3E,0x37,0x77,0x7E};
        m = load_program(hram, sizeof(hram));
        REQUIRE(m != NULL);
        r = gbb_run(m, 56, NULL, 0);
        REQUIRE(r.consumed_half_dots == 56);
        REQUIRE(gbb_peek_ram(m, 0xFF80) == 0x37);
        gbb_destroy(m);
        PASS("bus_echo_hram");
        return 0;
    }
    if (strcmp(argv[1], "absent_cart") == 0) {
        const uint8_t read_program[] = {0x21,0x00,0xA0,0x7E};
        gbb_instance *m = load_program(read_program, sizeof(read_program));
        REQUIRE(m != NULL);
        gbb_trace_record trace[4];
        gbb_run_result r = gbb_run(m, 32, trace, 4);
        REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS && r.consumed_half_dots == 24);
        REQUIRE(r.trace_count == 1 && trace[0].pc == 0x0100);
        gbb_destroy(m);
        const uint8_t write_program[] = {0x21,0x00,0xA0,0x3E,0x55,0x77};
        m = load_program(write_program, sizeof(write_program));
        REQUIRE(m != NULL);
        r = gbb_run(m, 48, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 40);
        REQUIRE(gbb_peek_ram(m, 0xA000) == 0xFF);
        gbb_destroy(m);
        PASS("bus_absent_cart");
        return 0;
    }
    if (strcmp(argv[1], "preflight") == 0) {
        const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x42,0x77};
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_trace_record trace[3];
        memset(trace, 0xA5, sizeof(trace));
        gbb_run_result short_run = gbb_run(m, 23, trace, 3);
        REQUIRE(short_run.reason == GBB_STOP_BUDGET && short_run.consumed_half_dots == 0);
        REQUIRE(short_run.trace_count == 0 && trace[0].pc == 0xA5A5);
        gbb_run_result exact = gbb_run(m, 24, trace, 3);
        REQUIRE(exact.consumed_half_dots == 24 && exact.trace_count == 1);
        REQUIRE(trace[0].pc == 0x0100 && trace[0].time_half_dots == 0);
        gbb_destroy(m);
        PASS("bus_preflight");
        return 0;
    }
    return 2;
}
