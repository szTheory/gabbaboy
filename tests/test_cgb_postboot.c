/* DMG post-boot pin (D-06). Pins the state the DMG-CPU-B profile starts in,
 * through the public API only, against literals typed here. The literals are
 * the values v0.1 shipped; they are deliberately NOT corrected toward Pan Docs
 * where the two differ (the DMG column records the implemented value).
 *
 * CPU registers come from gbb_test_cpu_snapshot before any guest runs. I/O
 * registers are read by a synthetic guest that LDH-loads each one and stores it
 * to consecutive HRAM bytes, so DIV, LY and STAT are exact because guest timing
 * is deterministic.
 *
 * `--flip N` XORs expected entry N with 1; the run must then fail naming the
 * field (negative control). */
#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);

typedef struct {
    const char *name;
    uint16_t address; /* 0 for CPU fields */
    uint16_t value;
} pin_entry;

#define CPU_FIELDS 10u

/* I/O read order: the guest reads these addresses in this order. */
static const pin_entry io_pin[] = {
    /* Time-dependent registers are read first so their values stay close to power-on. */
    {"STAT", 0xFF41, 0x86}, {"LY", 0xFF44, 0x00}, {"DIV", 0xFF04, 0xAB}, {"IF", 0xFF0F, 0xE0},
    {"P1", 0xFF00, 0xFF}, {"SB", 0xFF01, 0x00}, {"SC", 0xFF02, 0x7E},
    {"TIMA", 0xFF05, 0x00}, {"TMA", 0xFF06, 0x00}, {"TAC", 0xFF07, 0xF8},
    {"NR10", 0xFF10, 0x80}, {"NR11", 0xFF11, 0x3F}, {"NR12", 0xFF12, 0x00},
    {"NR13", 0xFF13, 0xFF}, {"NR14", 0xFF14, 0xBF},
    {"NR21", 0xFF16, 0x3F}, {"NR22", 0xFF17, 0x00}, {"NR23", 0xFF18, 0xFF},
    {"NR24", 0xFF19, 0xBF},
    {"NR30", 0xFF1A, 0x7F}, {"NR31", 0xFF1B, 0xFF}, {"NR32", 0xFF1C, 0x9F},
    {"NR33", 0xFF1D, 0xFF}, {"NR34", 0xFF1E, 0xBF},
    {"NR41", 0xFF20, 0xFF}, {"NR42", 0xFF21, 0x00}, {"NR43", 0xFF22, 0x00},
    {"NR44", 0xFF23, 0xBF},
    {"NR50", 0xFF24, 0x00}, {"NR51", 0xFF25, 0xFF}, {"NR52", 0xFF26, 0xF0},
    {"LCDC", 0xFF40, 0x91}, {"SCY", 0xFF42, 0x00},
    {"SCX", 0xFF43, 0x00}, {"LYC", 0xFF45, 0x00},
    {"DMA", 0xFF46, 0xFF}, {"BGP", 0xFF47, 0xFC}, {"OBP0", 0xFF48, 0xFF},
    {"OBP1", 0xFF49, 0xFF}, {"WY", 0xFF4A, 0x00}, {"WX", 0xFF4B, 0x00},
    {"IE", 0xFFFF, 0xE0},
};
#define IO_FIELDS (sizeof(io_pin) / sizeof(io_pin[0]))

static unsigned build_guest(uint8_t *code) {
    unsigned n = 0;
    for (unsigned i = 0; i < IO_FIELDS; ++i) {
        if (io_pin[i].address == 0xFFFFu) {
            code[n++] = 0xFA; code[n++] = 0xFF; code[n++] = 0xFF; /* LD A,(FFFF) */
        } else {
            code[n++] = 0xF0; code[n++] = (uint8_t)io_pin[i].address; /* LDH A,(n) */
        }
        code[n++] = 0xE0; code[n++] = (uint8_t)(0x80u + i); /* LDH (80+i),A */
    }
    code[n++] = 0x76; /* HALT: IE is zero so nothing wakes it */
    return n;
}

/* title_byte makes header byte $14D zero (0xE7) or non-zero (0x00). */
static gbb_instance *load_guest(uint8_t title_byte, const uint8_t *code, unsigned len) {
    uint8_t *rom = calloc(1, 32768);
    gbb_instance *m = NULL;
    if (rom == NULL) return NULL;
    /* The guest is too long for 0x100-0x133, so entry jumps past the header. */
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    memcpy(rom + 0x150, code, len);
    rom[0x134] = title_byte;
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK ||
        gbb_load_rom(m, rom, 32768) != GBB_OK) {
        gbb_destroy(m);
        m = NULL;
    }
    free(rom);
    return m;
}

static int check(const char *name, unsigned long expected, unsigned long actual,
                 long flip, unsigned index) {
    if ((long)index == flip) expected ^= 1u;
    if (expected != actual) {
        printf("not ok 1 - post-boot mismatch: %s expected 0x%lX got 0x%lX\n", name, expected, actual);
        fprintf(stderr, "post-boot mismatch: %s expected 0x%lX got 0x%lX\n", name, expected, actual);
        return 1;
    }
    return 0;
}

static int run_pin(uint8_t title_byte, uint8_t expected_f, long flip, const char *label) {
    uint8_t code[256];
    unsigned len = build_guest(code);
    gbb_instance *m = load_guest(title_byte, code, len);
    if (m == NULL) { printf("not ok 1 - load failed\n"); return 1; }

    gbb_trace_record cpu;
    gbb_test_cpu_snapshot(m, &cpu);
    const struct { const char *name; unsigned long expected, actual; } regs[CPU_FIELDS] = {
        {"A", 0x01, cpu.a}, {"F", expected_f, cpu.f}, {"B", 0x00, cpu.b},
        {"C", 0x13, cpu.c}, {"D", 0x00, cpu.d}, {"E", 0xD8, cpu.e},
        {"H", 0x01, cpu.h}, {"L", 0x4D, cpu.l}, {"SP", 0xFFFE, cpu.sp},
        {"PC", 0x0100, cpu.pc},
    };
    for (unsigned i = 0; i < CPU_FIELDS; ++i)
        if (check(regs[i].name, regs[i].expected, regs[i].actual, flip, i)) { gbb_destroy(m); return 1; }

    gbb_run_result r = gbb_run(m, 4096, NULL, 0);
    if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_HALTED_IDLE) {
        printf("not ok 1 - guest stopped unexpectedly (%d)\n", (int)r.reason);
        gbb_destroy(m);
        return 1;
    }
    for (unsigned i = 0; i < IO_FIELDS; ++i) {
        uint8_t got = gbb_peek_ram(m, (uint16_t)(0xFF80u + i));
        if (check(io_pin[i].name, io_pin[i].value, got, flip, CPU_FIELDS + i)) { gbb_destroy(m); return 1; }
    }
    gbb_destroy(m);
    printf("ok 1 - %s\n", label);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: test_cgb_postboot <dmg_pin|dmg_pin_checksum_zero> [--flip N]\n"); return 2; }
    long flip = -1;
    if (argc >= 4 && strcmp(argv[2], "--flip") == 0) flip = strtol(argv[3], NULL, 10);
    if (strcmp(argv[1], "dmg_pin") == 0) return run_pin(0x00, 0xB0, flip, "dmg_pin");
    if (strcmp(argv[1], "dmg_pin_checksum_zero") == 0) return run_pin(0xE7, 0x80, flip, "dmg_pin_checksum_zero");
    fprintf(stderr, "unknown case\n");
    return 2;
}
