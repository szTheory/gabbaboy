/* Post-boot pins (D-06, D-07). The first half pins the DMG column; the cases further down pin the
 * CGB-mode and compatibility columns of the CGB-CPU-E profile and prove channel 1 is silent.
 *
 * DMG post-boot pin (D-06). Pins the state the DMG-CPU-B profile starts in,
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

static unsigned build_reads(const pin_entry *table, unsigned count, uint8_t *code) {
    unsigned n = 0;
    for (unsigned i = 0; i < count; ++i) {
        if (table[i].address == 0xFFFFu) {
            code[n++] = 0xFA; code[n++] = 0xFF; code[n++] = 0xFF; /* LD A,(FFFF) */
        } else {
            code[n++] = 0xF0; code[n++] = (uint8_t)table[i].address; /* LDH A,(n) */
        }
        code[n++] = 0xE0; code[n++] = (uint8_t)(0x80u + i); /* LDH (80+i),A */
    }
    code[n++] = 0x76; /* HALT: IE is zero so nothing wakes it */
    return n;
}

static unsigned build_guest(uint8_t *code) { return build_reads(io_pin, (unsigned)IO_FIELDS, code); }

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

/* ---- CGB-CPU-E columns ---------------------------------------------------- */

typedef struct {
    uint8_t cgb_flag;
    uint8_t old_licensee;
    char new_licensee[2];
    uint8_t first_title_byte; /* the remaining title bytes are zero */
} header_spec;

/* A 32 KiB image: entry jumps to $150 where the guest lives; the header fields come from spec. */
static gbb_instance *load_profile(gbb_profile profile, const header_spec *spec,
                                  const uint8_t *code, unsigned len) {
    uint8_t *rom = calloc(1, 32768);
    gbb_instance *m = NULL;
    if (rom == NULL) return NULL;
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    if (len != 0) memcpy(rom + 0x150, code, len);
    rom[0x134] = spec->first_title_byte;
    rom[0x143] = spec->cgb_flag;
    rom[0x144] = (uint8_t)spec->new_licensee[0];
    rom[0x145] = (uint8_t)spec->new_licensee[1];
    rom[0x14B] = spec->old_licensee;
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
    if (gbb_create(profile, &m) != GBB_OK || gbb_load_rom(m, rom, 32768) != GBB_OK) {
        gbb_destroy(m);
        m = NULL;
    }
    free(rom);
    return m;
}

static gbb_instance *load_cgb(const header_spec *spec, const uint8_t *code, unsigned len) {
    return load_profile(GBB_PROFILE_CGB_CPU_E, spec, code, len);
}

typedef struct { unsigned a, f, b, c, d, e, h, l, sp, pc; } cpu_expect;

static int check_cpu(const gbb_instance *m, const cpu_expect *x, long flip, const char *label) {
    gbb_trace_record cpu;
    gbb_test_cpu_snapshot(m, &cpu);
    const struct { const char *name; unsigned long expected, actual; } regs[CPU_FIELDS] = {
        {"A", x->a, cpu.a}, {"F", x->f, cpu.f}, {"B", x->b, cpu.b}, {"C", x->c, cpu.c},
        {"D", x->d, cpu.d}, {"E", x->e, cpu.e}, {"H", x->h, cpu.h}, {"L", x->l, cpu.l},
        {"SP", x->sp, cpu.sp}, {"PC", x->pc, cpu.pc},
    };
    for (unsigned i = 0; i < CPU_FIELDS; ++i)
        if (check(regs[i].name, regs[i].expected, regs[i].actual, flip, i)) {
            fprintf(stderr, "case %s\n", label);
            return 1;
        }
    return 0;
}

static int run_cpu_case(const header_spec *spec, const cpu_expect *x, gbb_exec_mode mode,
                        const char *label) {
    gbb_instance *m = load_cgb(spec, NULL, 0);
    if (m == NULL) { printf("not ok 1 - load failed\n"); return 1; }
    gbb_info info = {0};
    info.struct_size = GBB_INFO_SIZE_V1;
    if (gbb_get_info(m, &info) != GBB_OK || info.mode != (uint32_t)mode) {
        printf("not ok 1 - %s: wrong execution mode %u\n", label, (unsigned)info.mode);
        gbb_destroy(m);
        return 1;
    }
    int rc = check_cpu(m, x, -1, label);
    gbb_destroy(m);
    if (rc == 0) printf("ok 1 - %s\n", label);
    return rc;
}

/* D-07: CGB-mode CPU row (Pan Docs, no hardware oracle). */
static const cpu_expect cgb_mode_cpu = {0x11, 0x80, 0x00, 0x00, 0xFF, 0x56, 0x00, 0x0D, 0xFFFE, 0x0100};

static int cgb_cpu_tracer(void) {
    const header_spec spec = {0x80, 0x00, {'Z', 'Z'}, 0x00};
    return run_cpu_case(&spec, &cgb_mode_cpu, GBB_MODE_CGB, "cgb_cpu_tracer");
}

/* D-07: compat CPU row (Mooneye boot_regs-cgb); F is $80 even though the checksum byte is not 0. */
static int compat_cpu(void) {
    const header_spec spec = {0x00, 0x00, {'Z', 'Z'}, 0x00};
    const cpu_expect x = {0x11, 0x80, 0x00, 0x00, 0x00, 0x08, 0x00, 0x7C, 0xFFFE, 0x0100};
    return run_cpu_case(&spec, &x, GBB_MODE_CGB_DMG_COMPAT, "compat_cpu");
}

/* No ROM loaded: the CGB profile is in its compatibility state (D-04). */
static int compat_no_rom(void) {
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &m) != GBB_OK) { printf("not ok 1 - create failed\n"); return 1; }
    const cpu_expect x = {0x11, 0x80, 0x00, 0x00, 0x00, 0x08, 0x00, 0x7C, 0xFFFE, 0x0100};
    int rc = check_cpu(m, &x, -1, "compat_no_rom");
    gbb_destroy(m);
    if (rc == 0) printf("ok 1 - compat_no_rom\n");
    return rc;
}

/* D-07: Pan Docs licensee title-sum rule for compat B and HL. */
static int compat_title_sum(void) {
    static const struct {
        header_spec spec;
        unsigned b, h, l;
        const char *name;
    } rows[] = {
        {{0x00, 0x01, {'Z', 'Z'}, 0x43}, 0x43, 0x99, 0x1A, "sum $43 -> HL $991A"},
        {{0x00, 0x01, {'Z', 'Z'}, 0x58}, 0x58, 0x99, 0x1A, "sum $58 -> HL $991A"},
        {{0x00, 0x01, {'Z', 'Z'}, 0x10}, 0x10, 0x00, 0x7C, "sum $10 -> HL $007C"},
        {{0x00, 0x33, {'0', '1'}, 0x58}, 0x58, 0x99, 0x1A, "new licensee 01 -> sum"},
        /* Negative controls: no licensee match means B is $00 whatever the title sums to. */
        {{0x00, 0x00, {'Z', 'Z'}, 0x43}, 0x00, 0x00, 0x7C, "licensee $00 -> B $00"},
        {{0x00, 0x33, {'0', '2'}, 0x43}, 0x00, 0x00, 0x7C, "new licensee 02 -> B $00"},
        {{0x00, 0x33, {'1', '0'}, 0x43}, 0x00, 0x00, 0x7C, "new licensee 10 -> B $00"},
        /* CGB mode ignores the rule entirely. */
        {{0x80, 0x01, {'Z', 'Z'}, 0x43}, 0x00, 0x00, 0x0D, "CGB mode ignores the sum"},
    };
    for (unsigned i = 0; i < sizeof(rows) / sizeof(rows[0]); ++i) {
        gbb_instance *m = load_cgb(&rows[i].spec, NULL, 0);
        if (m == NULL) { printf("not ok 1 - load failed\n"); return 1; }
        gbb_trace_record cpu;
        gbb_test_cpu_snapshot(m, &cpu);
        gbb_destroy(m);
        if (cpu.b != rows[i].b || cpu.h != rows[i].h || cpu.l != rows[i].l) {
            printf("not ok 1 - title sum row '%s': B=%02X H=%02X L=%02X\n", rows[i].name,
                   cpu.b, cpu.h, cpu.l);
            fprintf(stderr, "title sum row '%s' mismatch\n", rows[i].name);
            return 1;
        }
    }
    printf("ok 1 - compat_title_sum\n");
    return 0;
}

/* I/O literals, compat column (Mooneye boot_hwio-C where marked HW_TEST in the table). */
static const pin_entry compat_io[] = {
    {"IF", 0xFF0F, 0xE1}, {"P1", 0xFF00, 0xFF}, {"SC", 0xFF02, 0x7E}, {"DMA", 0xFF46, 0x00},
    {"NR11", 0xFF11, 0xBF}, {"NR12", 0xFF12, 0xF3}, {"NR50", 0xFF24, 0x77},
    {"NR51", 0xFF25, 0xF3}, {"NR52", 0xFF26, 0xF1},
};
/* CGB-mode column (Pan Docs; P1 from the SameBoy oracle). SC bit 0 reads 1. */
static const pin_entry cgb_io[] = {
    {"IF", 0xFF0F, 0xE1}, {"P1", 0xFF00, 0xFF}, {"SC", 0xFF02, 0x7F}, {"DMA", 0xFF46, 0x00},
    {"NR11", 0xFF11, 0xBF}, {"NR12", 0xFF12, 0xF3}, {"NR50", 0xFF24, 0x77},
    {"NR51", 0xFF25, 0xF3}, {"NR52", 0xFF26, 0xF1},
};
#define TABLE_LEN(t) ((unsigned)(sizeof(t) / sizeof((t)[0])))

static int run_io(const header_spec *spec, const pin_entry *table, unsigned count, long flip,
                  const char *label) {
    uint8_t code[256];
    unsigned len = build_reads(table, count, code);
    gbb_instance *m = load_cgb(spec, code, len);
    if (m == NULL) { printf("not ok 1 - load failed\n"); return 1; }
    gbb_run_result r = gbb_run(m, 4096, NULL, 0);
    if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_HALTED_IDLE) {
        printf("not ok 1 - guest stopped unexpectedly (%d)\n", (int)r.reason);
        gbb_destroy(m);
        return 1;
    }
    for (unsigned i = 0; i < count; ++i) {
        uint8_t got = gbb_peek_ram(m, (uint16_t)(0xFF80u + i));
        if (check(table[i].name, table[i].value, got, flip, i)) { gbb_destroy(m); return 1; }
    }
    gbb_destroy(m);
    printf("ok 1 - %s\n", label);
    return 0;
}

static int compat_io_case(long flip) {
    const header_spec spec = {0x00, 0x00, {'Z', 'Z'}, 0x00};
    return run_io(&spec, compat_io, TABLE_LEN(compat_io), flip, "compat_io");
}

static int cgb_io_case(long flip) {
    const header_spec spec = {0x80, 0x00, {'Z', 'Z'}, 0x00};
    return run_io(&spec, cgb_io, TABLE_LEN(cgb_io), flip, "cgb_io");
}

/* A2: channel 1 is enabled at hand-off but silent. Guest A loops reading NR52, TIMA and IF into HRAM
 * while the audio path runs; guest B (the control) retriggers channel 1 at volume $F first. */
#define AUDIO_CAPACITY 4096u

static unsigned silent_guest(uint8_t *c) {
    unsigned n = 0;
    c[n++] = 0xF0; c[n++] = 0x26; c[n++] = 0xE0; c[n++] = 0x80; /* NR52 -> FF80 */
    c[n++] = 0xF0; c[n++] = 0x05; c[n++] = 0xE0; c[n++] = 0x81; /* TIMA -> FF81 */
    c[n++] = 0xF0; c[n++] = 0x0F; c[n++] = 0xE0; c[n++] = 0x82; /* IF -> FF82 */
    c[n++] = 0xF0; c[n++] = 0x07; c[n++] = 0xE0; c[n++] = 0x83; /* TAC -> FF83 */
    c[n++] = 0x18; c[n] = (uint8_t)(0 - (int)(n + 1));              /* JR back to the start */
    return n + 1;
}

static unsigned control_guest(uint8_t *c) {
    unsigned n = 0;
    c[n++] = 0x3E; c[n++] = 0xF0; c[n++] = 0xE0; c[n++] = 0x12; /* NR12 = $F0: volume 15 */
    c[n++] = 0x3E; c[n++] = 0xFF; c[n++] = 0xE0; c[n++] = 0x13; /* NR13 = $FF */
    c[n++] = 0x3E; c[n++] = 0x87; c[n++] = 0xE0; c[n++] = 0x14; /* NR14 = trigger, frequency high 7 */
    c[n++] = 0x18; c[n++] = 0xFE;                               /* JR $ */
    return n;
}

static gbb_audio_frame frames[AUDIO_CAPACITY];

static unsigned distinct_frames(size_t count) {
    unsigned distinct = 0;
    for (size_t i = 0; i < count; ++i) {
        unsigned seen = 0;
        for (size_t j = 0; j < i && !seen; ++j)
            seen = frames[j].left == frames[i].left && frames[j].right == frames[i].right;
        if (!seen) ++distinct;
        if (distinct > 8) break;
    }
    return distinct;
}

static int run_audio_case(const header_spec *spec, int control, const char *label) {
    uint8_t code[64];
    unsigned len = control ? control_guest(code) : silent_guest(code);
    gbb_instance *m = load_cgb(spec, code, len);
    if (m == NULL) { printf("not ok 1 - load failed\n"); return 1; }
    size_t count = 0;
    /* Four video frames of master timeline (140448 half-dots each). */
    gbb_run_result r = gbb_run_audio(m, 4u * 140448u, frames, AUDIO_CAPACITY, &count);
    if (r.reason != GBB_STOP_BUDGET || count < 2000) {
        printf("not ok 1 - %s: run stopped (%d) after %zu frames\n", label, (int)r.reason, count);
        gbb_destroy(m);
        return 1;
    }
    const unsigned distinct = distinct_frames(count);
    if (!control) {
        const uint8_t nr52 = gbb_peek_ram(m, 0xFF80u), tima = gbb_peek_ram(m, 0xFF81u);
        const uint8_t iflag = gbb_peek_ram(m, 0xFF82u), tac = gbb_peek_ram(m, 0xFF83u);
        if (distinct != 1u || nr52 != 0xF1u || tima != 0u || (iflag & 0x04u) != 0u || tac != 0xF8u) {
            printf("not ok 1 - %s: distinct=%u NR52=%02X TIMA=%02X IF=%02X TAC=%02X\n", label,
                   distinct, nr52, tima, iflag, tac);
            fprintf(stderr, "%s: channel 1 is not silent or the timer moved\n", label);
            gbb_destroy(m);
            return 1;
        }
    } else if (distinct < 2u) {
        printf("not ok 1 - %s: a retriggered channel 1 produced only %u distinct PCM values\n",
               label, distinct);
        fprintf(stderr, "%s: control cannot hear sound\n", label);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int ch1_silent(void) {
    const header_spec compat = {0x00, 0x00, {'Z', 'Z'}, 0x00};
    const header_spec cgb = {0x80, 0x00, {'Z', 'Z'}, 0x00};
    if (run_audio_case(&compat, 0, "compat silent")) return 1;
    if (run_audio_case(&cgb, 0, "cgb silent")) return 1;
    if (run_audio_case(&compat, 1, "compat control")) return 1;
    if (run_audio_case(&cgb, 1, "cgb control")) return 1;
    printf("ok 1 - ch1_silent\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: test_cgb_postboot <case> [--flip N]\n"); return 2; }
    long flip = -1;
    if (argc >= 4 && strcmp(argv[2], "--flip") == 0) flip = strtol(argv[3], NULL, 10);
    if (strcmp(argv[1], "dmg_pin") == 0) return run_pin(0x00, 0xB0, flip, "dmg_pin");
    if (strcmp(argv[1], "dmg_pin_checksum_zero") == 0) return run_pin(0xE7, 0x80, flip, "dmg_pin_checksum_zero");
    if (strcmp(argv[1], "cgb_cpu_tracer") == 0) return cgb_cpu_tracer();
    if (strcmp(argv[1], "compat_cpu") == 0) return compat_cpu();
    if (strcmp(argv[1], "compat_no_rom") == 0) return compat_no_rom();
    if (strcmp(argv[1], "compat_title_sum") == 0) return compat_title_sum();
    if (strcmp(argv[1], "compat_io") == 0) return compat_io_case(flip);
    if (strcmp(argv[1], "cgb_io") == 0) return cgb_io_case(flip);
    if (strcmp(argv[1], "ch1_silent") == 0) return ch1_silent();
    fprintf(stderr, "unknown case\n");
    return 2;
}
