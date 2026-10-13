/* CGB register visibility behaviour cases (Plan 10-09; D-06, D-09, D-10, OQ2, OQ5).
 *
 * Each case builds a tiny original guest program, runs it through the public run API on the DMG
 * profile, the CGB profile in CGB mode ($143 = $80) and the CGB profile in compatibility mode
 * ($143 = $00), and reads results back from HRAM or through the stop reason. The exhaustive per-cell
 * matrix and its controls are Plan 10-10; these cases pin the decode, the deferred-access latch, the
 * IE gate, bank selection and the boundaries between mapped and unmapped neighbours.
 *
 * Usage: test_cgb_visibility <case> */
#include "gabbaboy/gabbaboy.h"
#include "gabbaboy_test.h"

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
extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);

/* The three views of one guest. */
typedef enum { V_DMG = 0, V_CGB, V_COMPAT, V_COUNT } view;
static const char *const view_names[V_COUNT] = { "DMG", "CGB", "COMPAT" };

static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}

/* The program sits at $150 behind a jump so it may exceed the header gap. vec40, when non-NULL,
 * is placed at the VBlank vector. */
static gbb_instance *load_view(view v, const uint8_t *program, size_t length,
                               const uint8_t *vec40, size_t vec40_length) {
    uint8_t *rom = calloc(1, 32768);
    gbb_instance *machine = NULL;
    if (rom == NULL) return NULL;
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    memcpy(rom + 0x150, program, length);
    if (vec40 != NULL) memcpy(rom + 0x40, vec40, vec40_length);
    rom[0x143] = v == V_CGB ? 0x80 : 0x00;
    fix_checksum(rom);
    if (gbb_create(v == V_DMG ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

/* Same atomic-rejection check as tests/test_bus.c: a refused pre-flight changes no guest-visible
 * state, emits no trace, diagnostic or bus event, and consumes no time. */
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

/* Tiny assembler. */
typedef struct { uint8_t b[600]; size_t n; } prog;
static void emit(prog *p, uint8_t x) { p->b[p->n++] = x; }
static void ld_a(prog *p, uint8_t v) { emit(p, 0x3E); emit(p, v); }
static void ldh_st(prog *p, uint8_t lo) { emit(p, 0xE0); emit(p, lo); }
static void ldh_ld(prog *p, uint8_t lo) { emit(p, 0xF0); emit(p, lo); }
static void st_abs(prog *p, uint16_t a) { emit(p, 0xEA); emit(p, (uint8_t)a); emit(p, (uint8_t)(a >> 8)); }
static void ld_abs(prog *p, uint16_t a) { emit(p, 0xFA); emit(p, (uint8_t)a); emit(p, (uint8_t)(a >> 8)); }
static void halt(prog *p) { emit(p, 0x76); }
static void write_io(prog *p, uint8_t lo, uint8_t v) { ld_a(p, v); ldh_st(p, lo); }
/* Read an FF00-page register and keep it in HRAM slot `slot` (FF80 + slot). */
static void keep_io(prog *p, uint8_t lo, uint8_t slot) { ldh_ld(p, lo); ldh_st(p, (uint8_t)(0x80u + slot)); }

static uint8_t hram(const gbb_instance *m, unsigned slot) { return gbb_peek_ram(m, (uint16_t)(0xFF80u + slot)); }

#define RUN_BUDGET 40000u

/* A one-read probe. Returns the byte read (0..255) or -1 when the read stops atomically with the
 * seam reporting `addr`; a harness fault is -2. */
static int probe(view v, const uint8_t *setup, size_t setup_len, uint16_t addr) {
    prog p = { {0}, 0 };
    if (setup_len != 0) memcpy(p.b, setup, setup_len);
    p.n = setup_len;
    if (addr == 0xFFFFu) ld_abs(&p, addr); else ldh_ld(&p, (uint8_t)addr);
    ldh_st(&p, 0xF0);
    halt(&p);
    gbb_instance *m = load_view(v, p.b, p.n, NULL, 0);
    if (m == NULL) return -2;
    gbb_run_result r = gbb_run(m, RUN_BUDGET, NULL, 0);
    int result;
    if (r.reason == GBB_STOP_UNSUPPORTED_BUS) {
        result = reject_atomically(m) == 0 && gbb_test_last_unsupported_address(m) == addr ? -1 : -2;
    } else {
        result = gbb_peek_ram(m, 0xFFF0u);
    }
    gbb_destroy(m);
    return result;
}

#define STOP (-1)
static int expect_probe(view v, const uint8_t *setup, size_t n, uint16_t addr, int expected) {
    const int got = probe(v, setup, n, addr);
    if (got != expected) {
        fprintf(stderr, "probe %s $%04X: got %d, expected %d\n", view_names[v], addr, got, expected);
        return 1;
    }
    return 0;
}

/* Tracer: one visibility row (VBK) drives decode and pre-flight end to end. */
static int case_vbk_tracer(void) {
    prog p = { {0}, 0 };
    write_io(&p, 0x40, 0x00);          /* LCD off: VRAM is always reachable */
    write_io(&p, 0x4F, 0x01);
    keep_io(&p, 0x4F, 0);              /* FF4F reads $FE | 1 */
    ld_a(&p, 0xAA); st_abs(&p, 0x8000); /* lands in bank 1 */
    write_io(&p, 0x4F, 0x00);
    ld_abs(&p, 0x8000); ldh_st(&p, 0x81); /* bank 0 is still clear */
    keep_io(&p, 0x4F, 2);              /* $FE */
    write_io(&p, 0x4F, 0x01);
    ld_abs(&p, 0x8000); ldh_st(&p, 0x83); /* bank 1 kept $AA */
    halt(&p);

    gbb_instance *m = load_view(V_CGB, p.b, p.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0xFF);
    REQUIRE(hram(m, 1) == 0x00);
    REQUIRE(hram(m, 2) == 0xFE);
    REQUIRE(hram(m, 3) == 0xAA);
    uint8_t vb = 9, wb = 9;
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 1 && wb == 1);
    gbb_destroy(m);

    /* Compatibility mode: the register reads $FE | bank and the bank never leaves 0, so a DMG ROM
     * cannot reach bank 1. */
    prog c = { {0}, 0 };
    write_io(&c, 0x40, 0x00);
    write_io(&c, 0x4F, 0x01);
    keep_io(&c, 0x4F, 0);
    halt(&c);
    m = load_view(V_COMPAT, c.b, c.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0xFE);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0);
    gbb_destroy(m);

    /* DMG: a read still stops atomically, a write is a silent no-op (C4). */
    prog d = { {0}, 0 };
    keep_io(&d, 0x4F, 0);
    m = load_view(V_DMG, d.b, d.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason == GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(reject_atomically(m) == 0);
    REQUIRE(gbb_test_last_unsupported_address(m) == 0xFF4F);
    gbb_destroy(m);

    prog w = { {0}, 0 };
    write_io(&w, 0x4F, 0x01);
    write_io(&w, 0x80, 0x07);          /* proves execution continued past the write */
    halt(&w);
    m = load_view(V_DMG, w.b, w.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0x07);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0 && wb == 1);
    gbb_destroy(m);
    PASS("cgb_visibility_vbk_tracer");
    return 0;
}

static int case_svbk_select(void) {
    prog p = { {0}, 0 };
    write_io(&p, 0x70, 0x00);
    keep_io(&p, 0x70, 0);                       /* $F8: raw 0 */
    ld_a(&p, 0x11); st_abs(&p, 0xD000);         /* bank 1 */
    write_io(&p, 0x70, 0x05);
    keep_io(&p, 0x70, 1);                       /* $FD */
    ld_a(&p, 0x55); st_abs(&p, 0xD000);         /* bank 5 */
    write_io(&p, 0x70, 0x08);                   /* only 3 bits are kept: raw 0 -> bank 1 */
    keep_io(&p, 0x70, 2);                       /* $F8 */
    ld_abs(&p, 0xD000); ldh_st(&p, 0x83);       /* $11 from bank 1 */
    write_io(&p, 0x70, 0x0D);                   /* raw 5 again */
    keep_io(&p, 0x70, 4);                       /* $FD */
    halt(&p);

    gbb_instance *m = load_view(V_CGB, p.b, p.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0xF8);
    REQUIRE(hram(m, 1) == 0xFD);
    REQUIRE(hram(m, 2) == 0xF8);
    REQUIRE(hram(m, 3) == 0x11);
    REQUIRE(hram(m, 4) == 0xFD);
    uint8_t vb, wb;
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(wb == 5);
    REQUIRE(gbb_peek_ram(m, 0xD000) == 0x55);   /* bank 5 holds the second store */
    REQUIRE(gbb_peek_ram(m, 0xF000) == 0x55);   /* echo follows the bank */
    REQUIRE(gbb_peek_ram(m, 0xC000) == 0x00);   /* C000 is never banked */
    gbb_destroy(m);

    /* Compatibility mode: FF70 reads $FF, the write is ignored and WRAM stays on bank 1. */
    prog c = { {0}, 0 };
    write_io(&c, 0x70, 0x05);
    keep_io(&c, 0x70, 0);
    ld_a(&c, 0x66); st_abs(&c, 0xD000);
    halt(&c);
    m = load_view(V_COMPAT, c.b, c.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0xFF);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(wb == 1);
    REQUIRE(gbb_peek_ram(m, 0xD000) == 0x66);
    gbb_destroy(m);

    /* DMG: read stops; write is a no-op and WRAM stays on bank 1. */
    const uint8_t none[1] = {0};
    REQUIRE(expect_probe(V_DMG, none, 0, 0xFF70, STOP) == 0);
    prog d = { {0}, 0 };
    write_io(&d, 0x70, 0x05);
    write_io(&d, 0x80, 0x01);
    halt(&d);
    m = load_view(V_DMG, d.b, d.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0x01);
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(wb == 1);
    gbb_destroy(m);
    PASS("cgb_visibility_svbk_select");
    return 0;
}

/* Addresses that no register owns on the CGB profile: a write is ignored and a read returns $FF in
 * both CGB columns, while the DMG profile keeps stopping on the ones it always stopped on. */
static int case_unmapped_cgb(void) {
    uint16_t addrs[64];
    size_t n = 0;
    addrs[n++] = 0xFF03;
    for (uint16_t a = 0xFF08; a <= 0xFF0E; ++a) addrs[n++] = a;
    addrs[n++] = 0xFF15;
    addrs[n++] = 0xFF1F;
    for (uint16_t a = 0xFF27; a <= 0xFF2F; ++a) addrs[n++] = a;
    addrs[n++] = 0xFF4E;
    addrs[n++] = 0xFF50;
    for (uint16_t a = 0xFF57; a <= 0xFF67; ++a) addrs[n++] = a;
    for (uint16_t a = 0xFF6D; a <= 0xFF6F; ++a) addrs[n++] = a;
    addrs[n++] = 0xFF71;
    for (uint16_t a = 0xFF78; a <= 0xFF7F; ++a) addrs[n++] = a;
    REQUIRE(n == 50); /* 1+7+1+1+9+1+1+17+3+1+8 */
    for (size_t i = 0; i < n; ++i) {
        const uint8_t setup[] = { 0x3E, 0x5A, 0xE0, (uint8_t)addrs[i] };
        REQUIRE(expect_probe(V_CGB, setup, sizeof(setup), addrs[i], 0xFF) == 0);
        REQUIRE(expect_probe(V_COMPAT, setup, sizeof(setup), addrs[i], 0xFF) == 0);
    }
    /* Control: the DMG profile still stops on a sample of them, so the probe distinguishes the
     * profiles rather than always seeing $FF. */
    const uint16_t dmg_stops[] = { 0xFF03, 0xFF0E, 0xFF15, 0xFF2F, 0xFF4E, 0xFF50, 0xFF67, 0xFF78, 0xFF7F };
    for (size_t i = 0; i < sizeof(dmg_stops) / sizeof(dmg_stops[0]); ++i)
        REQUIRE(expect_probe(V_DMG, NULL, 0, dmg_stops[i], STOP) == 0);
    PASS("cgb_visibility_unmapped_cgb");
    return 0;
}

typedef struct {
    const char *name;
    uint8_t setup[4];
    uint8_t setup_len;
    uint16_t address;
    int dmg, cgb, compat;
} boundary_cell;

static int case_boundaries(void) {
    static const boundary_cell cells[] = {
        /* FF4B / FF4C */
        { "FF4B WX",     {0x3E, 0x5A, 0xE0, 0x4B}, 4, 0xFF4B, 0x5A, 0x5A, 0x5A },
        { "FF4C KEY0",   {0}, 0, 0xFF4C, STOP, 0xFF, 0xFF },
        /* FF4F / FF50 */
        { "FF4F VBK",    {0}, 0, 0xFF4F, STOP, 0xFE, 0xFE },
        { "FF50",        {0}, 0, 0xFF50, STOP, 0xFF, 0xFF },
        /* FF74 and FF75 / FF76 */
        { "FF74 init",   {0}, 0, 0xFF74, STOP, 0x00, 0xFF },
        { "FF74 stored", {0x3E, 0x33, 0xE0, 0x74}, 4, 0xFF74, STOP, 0x33, 0xFF },
        { "FF75 init",   {0}, 0, 0xFF75, STOP, 0x8F, 0x8F },
        { "FF75 stored", {0x3E, 0xA5, 0xE0, 0x75}, 4, 0xFF75, STOP, 0xAF, 0xAF },
        { "FF76",        {0}, 0, 0xFF76, STOP, STOP, STOP },
        /* FF77 / FF78 */
        { "FF77",        {0}, 0, 0xFF77, STOP, STOP, STOP },
        { "FF78",        {0}, 0, 0xFF78, STOP, 0xFF, 0xFF },
        /* FF7F / FF80 */
        { "FF7F",        {0}, 0, 0xFF7F, STOP, 0xFF, 0xFF },
        { "FF80 HRAM",   {0x3E, 0x42, 0xE0, 0x80}, 4, 0xFF80, 0x42, 0x42, 0x42 },
    };
    for (size_t i = 0; i < sizeof(cells) / sizeof(cells[0]); ++i) {
        const boundary_cell *c = &cells[i];
        const int want[V_COUNT] = { c->dmg, c->cgb, c->compat };
        for (int v = 0; v < V_COUNT; ++v) {
            if (expect_probe((view)v, c->setup, c->setup_len, c->address, want[v]) != 0) {
                fprintf(stderr, "boundary cell %s\n", c->name);
                return 1;
            }
        }
    }
    PASS("cgb_visibility_boundaries");
    return 0;
}

/* Deferred accesses stop visibly. A read stops before it happens; a write is dropped and the stop
 * follows the retire of the instruction that issued it. */
static int case_deferred_stop(void) {
    /* Reads: the DEFERRED CGB-mode cells (RP, PCM12, PCM34); the stop is atomic and the seam names the address. */
    const uint16_t deferred_reads[] = { 0xFF56, 0xFF76, 0xFF77 };
    for (size_t i = 0; i < sizeof(deferred_reads) / sizeof(deferred_reads[0]); ++i)
        REQUIRE(expect_probe(V_CGB, NULL, 0, deferred_reads[i], STOP) == 0);
    /* Control: FF55 reads $FF in CGB mode (only its write is deferred) and compat reads ignore the
     * deferred rows, so a probe that always stopped would fail here. */
    REQUIRE(expect_probe(V_CGB, NULL, 0, 0xFF55, 0xFF) == 0);
    REQUIRE(expect_probe(V_COMPAT, NULL, 0, 0xFF56, 0xFF) == 0);
    REQUIRE(expect_probe(V_COMPAT, NULL, 0, 0xFF76, STOP) == 0);
    REQUIRE(expect_probe(V_COMPAT, NULL, 0, 0xFF77, STOP) == 0);

    /* Writes: LD A,1; LDH (55),A; LD A,7; LDH (80),A. */
    prog p = { {0}, 0 };
    ld_a(&p, 0x01);
    ldh_st(&p, 0x55);
    write_io(&p, 0x80, 0x07);
    keep_io(&p, 0x55, 1);
    halt(&p);
    gbb_instance *m = load_view(V_CGB, p.b, p.n, NULL, 0);
    REQUIRE(m != NULL);
    gbb_trace_record snap;
    gbb_run_result r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(gbb_test_last_unsupported_address(m) == 0xFF55);
    /* The instruction retired: JP (32) + LD A,n (16) + LDH (n),A (24) half dots, PC advanced past it. */
    REQUIRE(r.consumed_half_dots == 72);
    gbb_test_cpu_snapshot(m, &snap);
    REQUIRE(snap.pc == 0x0154);
    REQUIRE(hram(m, 0) == 0x00);
    /* The latch is cleared by the report: execution resumes, the write stayed dropped. */
    r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(hram(m, 0) == 0x07);
    REQUIRE(hram(m, 1) == 0xFF);
    gbb_destroy(m);

    /* Every deferred write cell stops in CGB mode with its own address. */
    const uint16_t deferred_writes[] = { 0xFF55, 0xFF56, 0xFF76, 0xFF77 };
    for (size_t i = 0; i < sizeof(deferred_writes) / sizeof(deferred_writes[0]); ++i) {
        prog w = { {0}, 0 };
        write_io(&w, (uint8_t)deferred_writes[i], 0x01);
        halt(&w);
        m = load_view(V_CGB, w.b, w.n, NULL, 0);
        REQUIRE(m != NULL);
        REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason == GBB_STOP_UNSUPPORTED_BUS);
        REQUIRE(gbb_test_last_unsupported_address(m) == deferred_writes[i]);
        gbb_destroy(m);
    }

    /* Compat mode ignores FF55/FF56 writes (no stop) but FF76/FF77 stay deferred;
     * the DMG profile never stops on any of them (C4). */
    for (size_t i = 0; i < sizeof(deferred_writes) / sizeof(deferred_writes[0]); ++i) {
        const int compat_stops = deferred_writes[i] >= 0xFF76;
        for (int v = V_DMG; v <= V_COMPAT; v += 2) {
            prog w = { {0}, 0 };
            write_io(&w, (uint8_t)deferred_writes[i], 0x01);
            write_io(&w, 0x80, 0x09);
            halt(&w);
            m = load_view((view)v, w.b, w.n, NULL, 0);
            REQUIRE(m != NULL);
            r = gbb_run(m, RUN_BUDGET, NULL, 0);
            if (v == V_COMPAT && compat_stops) {
                REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS);
            } else {
                REQUIRE(r.reason != GBB_STOP_UNSUPPORTED_BUS);
                REQUIRE(hram(m, 0) == 0x09);
            }
            gbb_destroy(m);
        }
    }
    PASS("cgb_visibility_deferred_stop");
    return 0;
}

static int case_ie_gate(void) {
    /* Read-back of the stored byte. */
    prog p = { {0}, 0 };
    ld_a(&p, 0x00); st_abs(&p, 0xFFFF); ld_abs(&p, 0xFFFF); ldh_st(&p, 0x80);
    ld_a(&p, 0xE0); st_abs(&p, 0xFFFF); ld_abs(&p, 0xFFFF); ldh_st(&p, 0x81);
    ld_a(&p, 0xFF); st_abs(&p, 0xFFFF); ld_abs(&p, 0xFFFF); ldh_st(&p, 0x82);
    halt(&p);
    const int expect[V_COUNT][3] = { { 0xE0, 0xE0, 0xFF }, { 0x00, 0xE0, 0xFF }, { 0x00, 0xE0, 0xFF } };
    for (int v = 0; v < V_COUNT; ++v) {
        gbb_instance *m = load_view((view)v, p.b, p.n, NULL, 0);
        REQUIRE(m != NULL);
        REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
        for (int k = 0; k < 3; ++k) {
            if (hram(m, (unsigned)k) != expect[v][k])
                fprintf(stderr, "ie_gate %s step %d: got %02X want %02X\n", view_names[v], k, hram(m, (unsigned)k), expect[v][k]);
            REQUIRE(hram(m, (unsigned)k) == expect[v][k]);
        }
        gbb_destroy(m);
    }

    /* Dispatch still masks with $1F: IE=$E1 with IF bit 0 vectors to $40 ... */
    const uint8_t vec[] = { 0x3E, 0x99, 0xE0, 0x90, 0x76 };   /* LD A,$99; LDH ($90),A; HALT */
    prog d = { {0}, 0 };
    ld_a(&d, 0xE1); st_abs(&d, 0xFFFF);
    write_io(&d, 0x0F, 0x01);
    emit(&d, 0xFB);                                           /* EI */
    emit(&d, 0x00); emit(&d, 0x00);
    halt(&d);
    for (int v = 0; v < V_COUNT; ++v) {
        gbb_instance *m = load_view((view)v, d.b, d.n, vec, sizeof(vec));
        REQUIRE(m != NULL);
        gbb_run(m, RUN_BUDGET, NULL, 0);
        REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x99);
        gbb_destroy(m);
    }
    /* ... and control: IE=$E0 has no dispatchable bit, so with every IF bit set nothing vectors.
     * On the CGB profile bits 5-7 are stored, so a dispatch here would prove the mask is missing. */
    prog n = { {0}, 0 };
    ld_a(&n, 0xE0); st_abs(&n, 0xFFFF);
    write_io(&n, 0x0F, 0x1F);
    emit(&n, 0xFB);
    emit(&n, 0x00); emit(&n, 0x00);
    halt(&n);
    for (int v = 0; v < V_COUNT; ++v) {
        gbb_instance *m = load_view((view)v, n.b, n.n, vec, sizeof(vec));
        REQUIRE(m != NULL);
        gbb_run(m, RUN_BUDGET, NULL, 0);
        REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x00);
        gbb_destroy(m);
    }
    PASS("cgb_visibility_ie_gate");
    return 0;
}

static int case_deferred_latch_interrupt(void) {
    /* A deferred write is the instruction right after EI, with an interrupt pending: the stop is
     * reported before the interrupt is taken, and the interrupt is taken on the next run. */
    const uint8_t vec[] = { 0x3E, 0x99, 0xE0, 0x90, 0x76 };
    prog p = { {0}, 0 };
    write_io(&p, 0xFF, 0x01);                  /* IE = $01 */
    write_io(&p, 0x0F, 0x01);                  /* IF = $01; A stays $01 */
    emit(&p, 0xFB);                            /* EI: IME rises after the next instruction */
    ldh_st(&p, 0x55);                          /* that next instruction is the deferred write */
    emit(&p, 0x00);
    halt(&p);
    gbb_instance *m = load_view(V_CGB, p.b, p.n, vec, sizeof(vec));
    REQUIRE(m != NULL);
    gbb_run_result r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(gbb_test_last_unsupported_address(m) == 0xFF55);
    REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x00);   /* not yet vectored */
    r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x99);   /* the pending interrupt is taken afterwards */
    gbb_destroy(m);

    /* The interrupt-entry push itself hits deferred registers: SP = $FF57 makes the push write
     * FF56 then FF55. The stop is reported at the entry boundary with the last refused address. */
    prog q = { {0}, 0 };
    emit(&q, 0x31); emit(&q, 0x57); emit(&q, 0xFF);    /* LD SP,$FF57 */
    write_io(&q, 0xFF, 0x01);
    write_io(&q, 0x0F, 0x01);
    emit(&q, 0xFB);
    emit(&q, 0x00); emit(&q, 0x00);
    halt(&q);
    m = load_view(V_CGB, q.b, q.n, vec, sizeof(vec));
    REQUIRE(m != NULL);
    r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(gbb_test_last_unsupported_address(m) == 0xFF55);
    gbb_trace_record snap;
    gbb_test_cpu_snapshot(m, &snap);
    REQUIRE(snap.pc == 0x0040);                 /* the entry completed; the vector has not run */
    REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x00);
    r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x99);
    gbb_destroy(m);

    /* Control: the same interrupt with an ordinary stack does not stop. */
    prog c = { {0}, 0 };
    write_io(&c, 0xFF, 0x01);
    write_io(&c, 0x0F, 0x01);
    emit(&c, 0xFB);
    emit(&c, 0x00); emit(&c, 0x00);
    halt(&c);
    m = load_view(V_CGB, c.b, c.n, vec, sizeof(vec));
    REQUIRE(m != NULL);
    r = gbb_run(m, RUN_BUDGET, NULL, 0);
    REQUIRE(r.reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(gbb_peek_ram(m, 0xFF90) == 0x99);
    gbb_destroy(m);
    PASS("cgb_visibility_deferred_latch_interrupt");
    return 0;
}

/* ---- Per-cell matrix (Plan 10-10, D-11) -------------------------------------------------------
 *
 * The table below is written from the D-10 decision table, not from io_visibility[] in the core, so
 * it is an independent oracle. One cell is one (column, address) pair:
 *   read0, then write w1, read1, write w2, read2
 * through the public API. A read expectation is a byte or STOP (the read stops atomically). The kind
 * says what a write does: IMPL writes are accepted or silently ignored; DEF_RW and DEF_W writes are
 * dropped and reported as a stop once the instruction retires (OQ5), tagged with the owning phase.
 * Each cell is run as up to three guest programs, one per read, so a read that stops does not hide
 * the reads after it. Earlier reads that stop are skipped in later programs. */
/* K_PORT is an implemented palette data port (address = index register + 1): the CPU lock would make
 * its reads depend on the PPU mode, so the program turns the LCD off first (the lock does not apply
 * then, D-12) and parks the index at 0 without auto-increment so each read sees the last write. */
typedef enum { K_IMPL = 0, K_DEF_RW, K_DEF_W, K_PORT } ckind;

typedef struct {
    view col;
    uint16_t addr;
    int r0;
    uint8_t w1;
    int r1;
    uint8_t w2;
    int r2;
    ckind kind;
    uint8_t phase;      /* owning phase of a DEFERRED cell, 0 for IMPL */
    const char *src;    /* evidence behind the expected bytes */
} cell;

#define MAX_CELLS 256
static int g_quiet;

static void cell_fail(const cell *c, const char *what, int a, int b) {
    if (g_quiet) return;
    fprintf(stderr, "cell %s $%04X: %s (got %d, expected %d)\n", view_names[c->col], c->addr, what, a, b);
}

/* Returns 0 when every read, stop and bank expectation of the cell holds in c->col. */
static int run_cell(const cell *c) {
    const int reads[3] = { c->r0, c->r1, c->r2 };
    const uint8_t writes[2] = { c->w1, c->w2 };
    const uint8_t lo = (uint8_t)c->addr;
    for (int target = 0; target < 3; ++target) {
        enum { WRITE_STOP = 1, READ_STOP = 2 };
        int expected[8], nexp = 0;
        prog p = { {0}, 0 };
        if (c->kind == K_PORT) {
            write_io(&p, 0x40, 0x00);                 /* LCD off */
            write_io(&p, (uint8_t)(lo - 1u), 0x00);   /* index register: index 0, no auto-increment */
        }
        for (int step = 0; step <= target; ++step) {
            if (step > 0) {
                write_io(&p, lo, writes[step - 1]);
                if (c->kind == K_DEF_RW || c->kind == K_DEF_W) expected[nexp++] = WRITE_STOP;
            }
            if (reads[step] != STOP) keep_io(&p, lo, (uint8_t)step);
            else if (step == target) { ldh_ld(&p, lo); expected[nexp++] = READ_STOP; }
        }
        halt(&p);
        gbb_instance *m = load_view(c->col, p.b, p.n, NULL, 0);
        if (m == NULL) { cell_fail(c, "load failed", 0, 0); return 1; }
        int idx = 0, read_stopped = 0, bad = 0;
        for (;;) {
            gbb_run_result r = gbb_run(m, RUN_BUDGET, NULL, 0);
            if (r.reason != GBB_STOP_UNSUPPORTED_BUS) break;
            if (idx >= nexp) { cell_fail(c, "unexpected stop", 1, 0); bad = 1; break; }
            if (gbb_test_last_unsupported_address(m) != c->addr) {
                cell_fail(c, "stop address", gbb_test_last_unsupported_address(m), c->addr); bad = 1; break;
            }
            if (expected[idx] == READ_STOP) {
                if (reject_atomically(m) != 0) { cell_fail(c, "read stop not atomic", 0, 1); bad = 1; }
                read_stopped = 1;
                ++idx;
                break;
            }
            /* A write stop follows a retired instruction, so the run consumed time. A refused read
             * consumes none; without this a read stuck on the same stop would pass for a write. */
            if (r.consumed_half_dots == 0) { cell_fail(c, "write stop consumed no time", 0, 1); bad = 1; break; }
            ++idx;
        }
        if (!bad && idx != nexp) { cell_fail(c, "stops seen", idx, nexp); bad = 1; }
        for (int step = 0; !bad && step <= target; ++step) {
            if (reads[step] == STOP) continue;
            if (step == target && read_stopped) continue;
            if (hram(m, (unsigned)step) != (unsigned)reads[step]) {
                cell_fail(c, step == 0 ? "read0" : step == 1 ? "read1" : "read2", hram(m, (unsigned)step), reads[step]);
                bad = 1;
            }
        }
        if (!bad && c->col != V_CGB) {
            /* Outside CGB mode no write may move either bank (D-15). */
            uint8_t vb = 9, wb = 9;
            gbb_test_bank_state(m, &vb, &wb);
            if (vb != 0 || wb != 1) { cell_fail(c, "bank moved", vb, 0); bad = 1; }
        }
        gbb_destroy(m);
        if (bad) return 1;
    }
    return 0;
}

static cell g_cells[MAX_CELLS];
static size_t g_ncells;

static void add_cell(view col, uint16_t addr, int r0, uint8_t w1, int r1, uint8_t w2, int r2,
                     ckind kind, uint8_t phase, const char *src) {
    cell c = { col, addr, r0, w1, r1, w2, r2, kind, phase, src };
    if (g_ncells < MAX_CELLS) g_cells[g_ncells++] = c;
}

/* Addresses that no register owns on the CGB profile (D-10 "other unused IO in FF00-FF7F"). */
static size_t unused_addresses(uint16_t *out) {
    size_t n = 0;
    out[n++] = 0xFF03;
    for (uint16_t a = 0xFF08; a <= 0xFF0E; ++a) out[n++] = a;
    out[n++] = 0xFF15;
    out[n++] = 0xFF1F;
    for (uint16_t a = 0xFF27; a <= 0xFF2F; ++a) out[n++] = a;
    out[n++] = 0xFF4E;
    out[n++] = 0xFF50;
    for (uint16_t a = 0xFF57; a <= 0xFF67; ++a) out[n++] = a;
    for (uint16_t a = 0xFF6D; a <= 0xFF6F; ++a) out[n++] = a;
    out[n++] = 0xFF71;
    for (uint16_t a = 0xFF78; a <= 0xFF7F; ++a) out[n++] = a;
    return n;
}

static void const_ff(view col, uint16_t a, uint8_t w1, uint8_t w2, const char *src) {
    add_cell(col, a, 0xFF, w1, 0xFF, w2, 0xFF, K_IMPL, 0, src);
}

/* Compatibility-mode column ($143 = $00 on the CGB profile). */
static void fill_compat(void) {
    uint16_t un[64];
    const size_t nun = unused_addresses(un);
    for (size_t i = 0; i < nun; ++i) const_ff(V_COMPAT, un[i], 0x5A, 0xA5, "unused_hwio-C");
    const_ff(V_COMPAT, 0xFF4C, 0x04, 0xC0, "D-10 KEY0 locked");
    const_ff(V_COMPAT, 0xFF4D, 0x01, 0xFE, "D-10 KEY1");
    add_cell(V_COMPAT, 0xFF4F, 0xFE, 0x01, 0xFE, 0xFE, 0xFE, K_IMPL, 0, "boot_hwio-C");
    for (uint16_t a = 0xFF51; a <= 0xFF54; ++a) const_ff(V_COMPAT, a, 0x5A, 0xA5, "D-10 HDMA1-4");
    const_ff(V_COMPAT, 0xFF55, 0x01, 0x80, "D-10 HDMA5");
    const_ff(V_COMPAT, 0xFF56, 0x01, 0xC1, "D-10 RP");
    add_cell(V_COMPAT, 0xFF68, 0xC8, 0x3A, 0x7A, 0x80, 0xC0, K_IMPL, 0, "boot_hwio-C");
    const_ff(V_COMPAT, 0xFF69, 0x5A, 0xA5, "D-10 BCPD");
    add_cell(V_COMPAT, 0xFF6A, 0xD0, 0x3A, 0x7A, 0x80, 0xC0, K_IMPL, 0, "boot_hwio-C");
    const_ff(V_COMPAT, 0xFF6B, 0x5A, 0xA5, "D-10 OCPD");
    const_ff(V_COMPAT, 0xFF6C, 0x01, 0xFE, "D-10 OPRI");
    const_ff(V_COMPAT, 0xFF70, 0x05, 0x08, "D-10 SVBK");
    add_cell(V_COMPAT, 0xFF72, 0x00, 0xA5, 0xA5, 0x5A, 0x5A, K_IMPL, 0, "D-10 FF72");
    add_cell(V_COMPAT, 0xFF73, 0x00, 0xA5, 0xA5, 0x5A, 0x5A, K_IMPL, 0, "D-10 FF73");
    const_ff(V_COMPAT, 0xFF74, 0xA5, 0x5A, "D-10 FF74");
    add_cell(V_COMPAT, 0xFF75, 0x8F, 0xA5, 0xAF, 0x5A, 0xDF, K_IMPL, 0, "D-10 FF75");
    add_cell(V_COMPAT, 0xFF76, STOP, 0x5A, STOP, 0xA5, STOP, K_DEF_RW, 14, "D-10 PCM12");
    add_cell(V_COMPAT, 0xFF77, STOP, 0x5A, STOP, 0xA5, STOP, K_DEF_RW, 14, "D-10 PCM34");
}

/* CGB-mode column ($143 = $80). */
static void fill_cgb(void) {
    uint16_t un[64];
    const size_t nun = unused_addresses(un);
    for (size_t i = 0; i < nun; ++i) const_ff(V_CGB, un[i], 0x5A, 0xA5, "unused_hwio-C");
    const_ff(V_CGB, 0xFF4C, 0x04, 0xC0, "D-12 KEY0 locked");
    add_cell(V_CGB, 0xFF4D, 0x7E, 0x01, 0x7F, 0xFE, 0x7E, K_IMPL, 0, "D-10 KEY1 armed bit");
    add_cell(V_CGB, 0xFF4F, 0xFE, 0x01, 0xFF, 0xFE, 0xFE, K_IMPL, 0, "D-10 VBK");
    for (uint16_t a = 0xFF51; a <= 0xFF54; ++a) const_ff(V_CGB, a, 0x5A, 0xA5, "D-10 HDMA1-4");
    add_cell(V_CGB, 0xFF55, 0xFF, 0x01, 0xFF, 0x80, 0xFF, K_DEF_W, 13, "D-10 HDMA5");
    add_cell(V_CGB, 0xFF56, STOP, 0x01, STOP, 0xC1, STOP, K_DEF_RW, 14, "D-10 RP");
    add_cell(V_CGB, 0xFF68, 0xC0, 0x3A, 0x7A, 0x80, 0xC0, K_IMPL, 0, "D-10 BCPS");
    /* D-11: with the index parked at 0 both writes land there and read back whole. CRAM starts
     * white (D-14), so the first read is the low byte of $7FFF. */
    add_cell(V_CGB, 0xFF69, 0xFF, 0x5A, 0x5A, 0xA5, 0xA5, K_PORT, 0, "D-10/D-11 BCPD");
    add_cell(V_CGB, 0xFF6A, 0xC0, 0x3A, 0x7A, 0x80, 0xC0, K_IMPL, 0, "D-10 OCPS");
    add_cell(V_CGB, 0xFF6B, 0xFF, 0x5A, 0x5A, 0xA5, 0xA5, K_PORT, 0, "D-10/D-11 OCPD");
    /* D-08: OPRI starts 0 and keeps only bit 0: $FE | 0, write 1 -> $FF, write $FE -> $FE. */
    add_cell(V_CGB, 0xFF6C, 0xFE, 0x01, 0xFF, 0xFE, 0xFE, K_IMPL, 0, "D-08 OPRI");
    add_cell(V_CGB, 0xFF70, 0xF8, 0x05, 0xFD, 0x08, 0xF8, K_IMPL, 0, "D-10 SVBK");
    add_cell(V_CGB, 0xFF72, 0x00, 0xA5, 0xA5, 0x5A, 0x5A, K_IMPL, 0, "D-10 FF72");
    add_cell(V_CGB, 0xFF73, 0x00, 0xA5, 0xA5, 0x5A, 0x5A, K_IMPL, 0, "D-10 FF73");
    add_cell(V_CGB, 0xFF74, 0x00, 0xA5, 0xA5, 0x5A, 0x5A, K_IMPL, 0, "D-10 FF74");
    add_cell(V_CGB, 0xFF75, 0x8F, 0xA5, 0xAF, 0x5A, 0xDF, K_IMPL, 0, "D-10 FF75");
    add_cell(V_CGB, 0xFF76, STOP, 0x5A, STOP, 0xA5, STOP, K_DEF_RW, 14, "D-10 PCM12");
    add_cell(V_CGB, 0xFF77, STOP, 0x5A, STOP, 0xA5, STOP, K_DEF_RW, 14, "D-10 PCM34");
}

/* DMG column (D-09): every address that is not a pre-CGB register stops on read, atomically, and a
 * write is a silent no-op. The write values reuse the CGB ones so the same stores are attempted. */
static void fill_dmg(void) {
    uint16_t un[64];
    const size_t nun = unused_addresses(un);
    for (size_t i = 0; i < nun; ++i) add_cell(V_DMG, un[i], STOP, 0x5A, STOP, 0xA5, STOP, K_IMPL, 0, "unused_hwio-GS (fail-closed, D-09)");
    static const uint16_t regs[] = {
        0xFF4C, 0xFF4D, 0xFF4F, 0xFF51, 0xFF52, 0xFF53, 0xFF54, 0xFF55, 0xFF56,
        0xFF68, 0xFF69, 0xFF6A, 0xFF6B, 0xFF6C, 0xFF70, 0xFF72, 0xFF73, 0xFF74, 0xFF75, 0xFF76, 0xFF77
    };
    for (size_t i = 0; i < sizeof(regs) / sizeof(regs[0]); ++i)
        add_cell(V_DMG, regs[i], STOP, 0x05, STOP, 0xFE, STOP, K_IMPL, 0, "D-09 DMG FF4C-FF7F fail-closed");
}

static void build_table(void) {
    g_ncells = 0;
    fill_compat();
    fill_cgb();
    fill_dmg();
}

static int run_view_cells(view col, const char *name) {
    build_table();
    size_t n = 0;
    for (size_t i = 0; i < g_ncells; ++i) {
        if (g_cells[i].col != col) continue;
        ++n;
        if (run_cell(&g_cells[i]) != 0) return 1;
    }
    REQUIRE(n > 0);
    printf("ok 1 - %s cells=%zu\n", name, n);
    return 0;
}

static int case_matrix_compat(void) { return run_view_cells(V_COMPAT, "cgb_visibility_matrix_compat"); }
static int case_matrix_cgb(void) { return run_view_cells(V_CGB, "cgb_visibility_matrix_cgb"); }
static int case_matrix_dmg(void) { return run_view_cells(V_DMG, "cgb_visibility_matrix_dmg"); }

static int same_expectation(const cell *a, const cell *b) {
    return a->r0 == b->r0 && a->r1 == b->r1 && a->r2 == b->r2 && a->kind == b->kind;
}

/* Negative control: every cell whose expectation differs between two columns must fail when its
 * expectation is run in the other column. A differing cell that passes anywhere would mean the
 * columns are not actually distinguished by the probe. Identical cells are counted, not run. */
static int case_cross_column_control(void) {
    build_table();
    size_t checked[V_COUNT][V_COUNT] = {{0}}, same = 0;
    g_quiet = 1;
    int status = 0;
    for (size_t i = 0; i < g_ncells && !status; ++i) {
        for (size_t j = 0; j < g_ncells; ++j) {
            if (g_cells[j].addr != g_cells[i].addr || g_cells[j].col == g_cells[i].col) continue;
            if (same_expectation(&g_cells[i], &g_cells[j])) { ++same; continue; }
            cell moved = g_cells[i];
            moved.col = g_cells[j].col;
            if (run_cell(&moved) == 0) {
                g_quiet = 0;
                fprintf(stderr, "cross-column: %s expectation for $%04X also passes in %s\n",
                        view_names[g_cells[i].col], g_cells[i].addr, view_names[moved.col]);
                status = 1;
                break;
            }
            ++checked[g_cells[i].col][moved.col];
        }
    }
    g_quiet = 0;
    REQUIRE(status == 0);
    for (int a = 0; a < V_COUNT; ++a)
        for (int b = 0; b < V_COUNT; ++b)
            if (a != b) {
                if (checked[a][b] == 0) fprintf(stderr, "cross-column: no differing cell %s -> %s\n", view_names[a], view_names[b]);
                REQUIRE(checked[a][b] > 0);
            }
    printf("ok 1 - cgb_visibility_cross_column_control differing=%zu identical=%zu\n",
           checked[V_CGB][V_COMPAT] + checked[V_COMPAT][V_CGB] + checked[V_DMG][V_CGB] + checked[V_DMG][V_COMPAT] +
           checked[V_CGB][V_DMG] + checked[V_COMPAT][V_DMG], same);
    return 0;
}

/* Addresses whose behaviour is identical on every profile because the pre-CGB code owns them; the
 * existing bus_, timer_, serial_, apu_ and ppu_ tests cover them. Every other FF00-FF7F address
 * needs a row in each column. */
typedef struct { uint16_t lo, hi; } addr_range;
static const addr_range existing_ranges[] = {
    { 0xFF00, 0xFF02 }, { 0xFF04, 0xFF07 }, { 0xFF0F, 0xFF14 }, { 0xFF16, 0xFF1E },
    { 0xFF20, 0xFF26 }, { 0xFF30, 0xFF4B },
};
#define N_EXISTING (sizeof(existing_ranges) / sizeof(existing_ranges[0]))

/* Returns 0 when every FF00-FF7F address is exactly one of: in an existing range (and then has no
 * row), or has exactly one row per column. `skip_range` hides one range to model a gap. */
static int sweep_complete(const cell *t, size_t n, int skip_range, uint16_t *where) {
    for (uint32_t a = 0xFF00; a <= 0xFF7F; ++a) {
        int existing = 0;
        for (size_t r = 0; r < N_EXISTING; ++r)
            if ((int)r != skip_range && a >= existing_ranges[r].lo && a <= existing_ranges[r].hi) existing = 1;
        unsigned count[V_COUNT] = {0};
        for (size_t i = 0; i < n; ++i)
            if (t[i].addr == a) ++count[t[i].col];
        for (int v = 0; v < V_COUNT; ++v) {
            if (count[v] != (existing ? 0u : 1u)) { *where = (uint16_t)a; return 1; }
        }
    }
    return 0;
}

static int case_sweep_control(void) {
    build_table();
    uint16_t where = 0;
    REQUIRE(sweep_complete(g_cells, g_ncells, -1, &where) == 0);
    static cell local[MAX_CELLS];
    /* Deleting any one row makes the sweep report that address. */
    for (size_t drop = 0; drop < g_ncells; ++drop) {
        size_t m = 0;
        for (size_t i = 0; i < g_ncells; ++i)
            if (i != drop) local[m++] = g_cells[i];
        REQUIRE(sweep_complete(local, m, -1, &where) != 0);
        REQUIRE(where == g_cells[drop].addr);
    }
    /* Duplicating a row is also reported. */
    memcpy(local, g_cells, g_ncells * sizeof(cell));
    local[g_ncells] = g_cells[0];
    REQUIRE(sweep_complete(local, g_ncells + 1, -1, &where) != 0);
    /* Removing an existing range exposes its addresses as rowless. */
    for (size_t r = 0; r < N_EXISTING; ++r) {
        REQUIRE(sweep_complete(g_cells, g_ncells, (int)r, &where) != 0);
        REQUIRE(where == existing_ranges[r].lo);
    }
    /* Every FF4C-FF7F address has all three columns (D-11). */
    for (uint32_t a = 0xFF4C; a <= 0xFF7F; ++a) {
        unsigned count = 0;
        for (size_t i = 0; i < g_ncells; ++i) count += g_cells[i].addr == a;
        REQUIRE(count == 3);
    }
    printf("ok 1 - cgb_visibility_sweep_control rows=%zu\n", g_ncells);
    return 0;
}

/* Negative control: a copy of one compat row with a single expected byte flipped must be reported
 * as a failure, so a passing matrix is not vacuous. */
static int case_flip_control(void) {
    build_table();
    size_t picked = 0;
    for (size_t i = 0; i < g_ncells; ++i)
        if (g_cells[i].col == V_COMPAT && g_cells[i].addr == 0xFF4F) picked = i;
    cell good = g_cells[picked];
    REQUIRE(good.addr == 0xFF4F && run_cell(&good) == 0);
    g_quiet = 1;
    cell bad = good;
    bad.r1 ^= 0x01;                 /* the read after the first write */
    const int flipped_read = run_cell(&bad);
    bad = good;
    bad.r0 = STOP;                  /* a read expected to stop that does not */
    const int flipped_stop = run_cell(&bad);
    bad = good;
    bad.kind = K_DEF_W;             /* a write expected to stop that does not */
    const int flipped_kind = run_cell(&bad);
    g_quiet = 0;
    REQUIRE(flipped_read != 0);
    REQUIRE(flipped_stop != 0);
    REQUIRE(flipped_kind != 0);
    PASS("cgb_visibility_flip_control");
    return 0;
}

/* ---- STOP with KEY1 armed (Phase 12; D-23) ------------------------------------------------------
 * On the CGB profile, CGB-mode STOP with KEY1 armed switches speed and continues to the marker. */
static void stop_op(prog *p) { emit(p, 0x10); emit(p, 0x00); }

/* Runs [arm KEY1 if requested] STOP, then a marker store and HALT. Returns the first run reason. */
static int run_stop(view v, int arm, gbb_run_result *first, uint16_t *seam, int *second_reason, int *marker) {
    prog p = { {0}, 0 };
    if (arm) write_io(&p, 0x4D, 0x01);
    stop_op(&p);
    write_io(&p, 0x80, 0x5A);
    halt(&p);
    gbb_instance *m = load_view(v, p.b, p.n, NULL, 0);
    if (m == NULL) return 1;
    *first = gbb_run(m, 140448u, NULL, 0);
    *seam = gbb_test_last_unsupported_address(m);
    *second_reason = (int)first->reason;
    *marker = hram(m, 0);
    for (unsigned frame = 0; frame < 3u && *marker != 0x5Au; ++frame) {
        gbb_run_result next = gbb_run(m, 140448u, NULL, 0);
        *second_reason = (int)next.reason;
        *marker = hram(m, 0);
        fprintf(stderr, "frame %u reason=%d marker=%02x\n", frame, next.reason, *marker);
        if (next.reason == GBB_STOP_STOPPED || next.reason == GBB_STOP_UNSUPPORTED_BUS) break;
    }
    gbb_destroy(m);
    return 0;
}

static int case_stop_armed_cgb(void) {
    gbb_run_result r; uint16_t seam; int second, marker;
    REQUIRE(run_stop(V_CGB, 1, &r, &seam, &second, &marker) == 0);
    REQUIRE(r.reason != GBB_STOP_UNSUPPORTED_BUS);
    REQUIRE(r.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(seam != 0xFF4D);
    REQUIRE(second == (int)GBB_STOP_HALTED_IDLE);
    REQUIRE(marker != 0x5A);
    /* Control: without the arming write the same program does sleep, so the stop above is caused by
     * KEY1 and not by STOP itself. */
    gbb_run_result u; int s2, m2;
    REQUIRE(run_stop(V_CGB, 0, &u, &seam, &s2, &m2) == 0);
    REQUIRE(u.reason == GBB_STOP_STOPPED);
    PASS("cgb_stop_armed_cgb");
    return 0;
}

static int case_stop_unarmed_cgb(void) {
    gbb_run_result r; uint16_t seam; int second, marker;
    REQUIRE(run_stop(V_CGB, 0, &r, &seam, &second, &marker) == 0);
    REQUIRE(r.reason == GBB_STOP_STOPPED);
    /* Arming then disarming returns to the shared path. */
    prog p = { {0}, 0 };
    write_io(&p, 0x4D, 0x01);
    write_io(&p, 0x4D, 0x00);
    stop_op(&p);
    halt(&p);
    gbb_instance *m = load_view(V_CGB, p.b, p.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason == GBB_STOP_STOPPED);
    gbb_destroy(m);
    PASS("cgb_stop_unarmed_cgb");
    return 0;
}

static int case_stop_compat_ignores_key1(void) {
    gbb_run_result r; uint16_t seam; int second, marker;
    REQUIRE(run_stop(V_COMPAT, 1, &r, &seam, &second, &marker) == 0);
    REQUIRE(r.reason == GBB_STOP_STOPPED);
    PASS("cgb_stop_compat_ignores_key1");
    return 0;
}

static int case_stop_dmg_control(void) {
    gbb_run_result r; uint16_t seam; int second, marker;
    REQUIRE(run_stop(V_DMG, 1, &r, &seam, &second, &marker) == 0);
    REQUIRE(r.reason == GBB_STOP_STOPPED);
    PASS("cgb_stop_dmg_control");
    return 0;
}

/* ---- KEY0 lock (Plan 10-11; D-12) ------------------------------------------------------------- */
typedef struct {
    uint8_t key0[4];   /* read-back after writing $00, $04, $80, $C0 */
    uint8_t seq2[4];   /* the same sequence repeated */
    uint8_t vbk_after_write1;
    uint8_t vbk_after_write0;
    uint8_t vram8000;
    int mode_before, mode_after;
    int mode_after_reset;
    int rc;
} key0_result;

static void key0_sequence(prog *p, unsigned first_slot) {
    static const uint8_t values[4] = { 0x00, 0x04, 0x80, 0xC0 };
    for (unsigned i = 0; i < 4; ++i) {
        write_io(p, 0x4C, values[i]);
        keep_io(p, 0x4C, (uint8_t)(first_slot + i));
    }
}

static key0_result run_key0(view v, int repeat_sequence, int resets) {
    key0_result out;
    memset(&out, 0, sizeof(out));
    out.rc = 1;
    prog p = { {0}, 0 };
    write_io(&p, 0x40, 0x00);                 /* LCD off: VRAM always reachable */
    key0_sequence(&p, 0);
    if (repeat_sequence) key0_sequence(&p, 4);
    write_io(&p, 0x4F, 0x01);
    keep_io(&p, 0x4F, 8);
    ld_a(&p, 0x5A); st_abs(&p, 0x8000);
    write_io(&p, 0x4F, 0x00);
    keep_io(&p, 0x4F, 9);
    ld_abs(&p, 0x8000); ldh_st(&p, 0x8A);
    halt(&p);
    gbb_instance *m = load_view(v, p.b, p.n, NULL, 0);
    if (m == NULL) return out;
    gbb_info info;
    memset(&info, 0, sizeof(info));
    info.struct_size = sizeof(info);
    if (gbb_get_info(m, &info) != GBB_OK) { gbb_destroy(m); return out; }
    out.mode_before = (int)info.mode;
    if (gbb_run(m, RUN_BUDGET, NULL, 0).reason == GBB_STOP_UNSUPPORTED_BUS) { gbb_destroy(m); return out; }
    if (gbb_get_info(m, &info) != GBB_OK) { gbb_destroy(m); return out; }
    out.mode_after = (int)info.mode;
    for (unsigned i = 0; i < 4; ++i) { out.key0[i] = hram(m, i); out.seq2[i] = hram(m, 4 + i); }
    out.vbk_after_write1 = hram(m, 8);
    out.vbk_after_write0 = hram(m, 9);
    out.vram8000 = hram(m, 10);
    out.mode_after_reset = out.mode_after;
    for (int i = 0; i < resets; ++i) {
        if (gbb_reset(m) != GBB_OK || gbb_get_info(m, &info) != GBB_OK) { gbb_destroy(m); return out; }
        out.mode_after_reset = (int)info.mode;
    }
    gbb_destroy(m);
    out.rc = 0;
    return out;
}

/* Expectations for each column, written from the hardware description (KEY0 reads $FF; VBK is
 * live in CGB mode only), not from the code's output. */
static int key0_matches_cgb(const key0_result *r) {
    for (unsigned i = 0; i < 4; ++i) if (r->key0[i] != 0xFF) return 0;
    return r->vbk_after_write1 == 0xFF && r->vbk_after_write0 == 0xFE && r->vram8000 == 0x00 &&
           r->mode_before == GBB_MODE_CGB && r->mode_after == GBB_MODE_CGB;
}
static int key0_matches_compat(const key0_result *r) {
    for (unsigned i = 0; i < 4; ++i) if (r->key0[i] != 0xFF) return 0;
    return r->vbk_after_write1 == 0xFE && r->vbk_after_write0 == 0xFE && r->vram8000 == 0x5A &&
           r->mode_before == GBB_MODE_CGB_DMG_COMPAT && r->mode_after == GBB_MODE_CGB_DMG_COMPAT;
}

static int case_key0_lock_cgb(void) {
    key0_result r = run_key0(V_CGB, 0, 0);
    REQUIRE(r.rc == 0);
    REQUIRE(key0_matches_cgb(&r));
    PASS("cgb_key0_lock_cgb");
    return 0;
}

static int case_key0_lock_compat(void) {
    key0_result r = run_key0(V_COMPAT, 0, 0);
    REQUIRE(r.rc == 0);
    REQUIRE(key0_matches_compat(&r));
    PASS("cgb_key0_lock_compat");
    return 0;
}

static int case_key0_lock_cross_column(void) {
    key0_result cgb = run_key0(V_CGB, 0, 0), compat = run_key0(V_COMPAT, 0, 0);
    REQUIRE(cgb.rc == 0 && compat.rc == 0);
    /* Each column's expectation must reject the other column's run, otherwise the probe cannot
     * tell the two apart and the lock test could not fail. */
    if (key0_matches_compat(&cgb) || key0_matches_cgb(&compat)) {
        printf("not ok 1 - key0 control: columns indistinguishable\n");
        return 1;
    }
    REQUIRE(key0_matches_cgb(&cgb) && key0_matches_compat(&compat));
    /* A KEY0 that unlocked would change a read-back: a mutated copy must be rejected. */
    key0_result mutated = cgb;
    mutated.key0[2] = 0x80;
    REQUIRE(!key0_matches_cgb(&mutated));
    PASS("cgb_key0_lock_cross_column");
    return 0;
}

static int case_key0_lock_reset_idempotent(void) {
    for (int v = V_CGB; v <= V_COMPAT; ++v) {
        key0_result once = run_key0((view)v, 1, 0), twice = run_key0((view)v, 1, 2);
        REQUIRE(once.rc == 0 && twice.rc == 0);
        REQUIRE(memcmp(once.key0, once.seq2, 4) == 0);          /* repeating the writes changes nothing */
        REQUIRE(memcmp(once.key0, twice.key0, 4) == 0 && memcmp(once.seq2, twice.seq2, 4) == 0);
        REQUIRE(once.mode_before == once.mode_after && twice.mode_after_reset == twice.mode_before);
        REQUIRE(once.vram8000 == twice.vram8000 && once.vbk_after_write1 == twice.vbk_after_write1);
    }
    /* Reset is idempotent on the info block: two resets give byte-identical gbb_get_info output. */
    prog p = { {0}, 0 };
    key0_sequence(&p, 0);
    halt(&p);
    gbb_instance *m = load_view(V_CGB, p.b, p.n, NULL, 0);
    REQUIRE(m != NULL);
    REQUIRE(gbb_run(m, RUN_BUDGET, NULL, 0).reason != GBB_STOP_UNSUPPORTED_BUS);
    gbb_info a, b;
    memset(&a, 0, sizeof(a)); memset(&b, 0, sizeof(b));
    a.struct_size = b.struct_size = sizeof(a);
    REQUIRE(gbb_reset(m) == GBB_OK && gbb_get_info(m, &a) == GBB_OK);
    REQUIRE(gbb_reset(m) == GBB_OK && gbb_get_info(m, &b) == GBB_OK);
    REQUIRE(a.mode == b.mode && a.mode == GBB_MODE_CGB);
    REQUIRE(memcmp(&a, &b, sizeof(a)) == 0);
    gbb_destroy(m);
    PASS("cgb_key0_lock_reset_idempotent");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_cgb_visibility <case>\n");
        return 2;
    }
    if (strcmp(argv[1], "vbk_tracer") == 0) return case_vbk_tracer();
    if (strcmp(argv[1], "svbk_select") == 0) return case_svbk_select();
    if (strcmp(argv[1], "unmapped_cgb") == 0) return case_unmapped_cgb();
    if (strcmp(argv[1], "boundaries") == 0) return case_boundaries();
    if (strcmp(argv[1], "deferred_stop") == 0) return case_deferred_stop();
    if (strcmp(argv[1], "ie_gate") == 0) return case_ie_gate();
    if (strcmp(argv[1], "deferred_latch_interrupt") == 0) return case_deferred_latch_interrupt();
    if (strcmp(argv[1], "matrix_compat") == 0) return case_matrix_compat();
    if (strcmp(argv[1], "flip_control") == 0) return case_flip_control();
    if (strcmp(argv[1], "matrix_cgb") == 0) return case_matrix_cgb();
    if (strcmp(argv[1], "matrix_dmg") == 0) return case_matrix_dmg();
    if (strcmp(argv[1], "cross_column_control") == 0) return case_cross_column_control();
    if (strcmp(argv[1], "sweep_control") == 0) return case_sweep_control();
    if (strcmp(argv[1], "stop_armed_cgb") == 0) return case_stop_armed_cgb();
    if (strcmp(argv[1], "stop_unarmed_cgb") == 0) return case_stop_unarmed_cgb();
    if (strcmp(argv[1], "stop_compat_ignores_key1") == 0) return case_stop_compat_ignores_key1();
    if (strcmp(argv[1], "stop_dmg_control") == 0) return case_stop_dmg_control();
    if (strcmp(argv[1], "key0_lock_cgb") == 0) return case_key0_lock_cgb();
    if (strcmp(argv[1], "key0_lock_compat") == 0) return case_key0_lock_compat();
    if (strcmp(argv[1], "key0_lock_cross_column") == 0) return case_key0_lock_cross_column();
    if (strcmp(argv[1], "key0_lock_reset_idempotent") == 0) return case_key0_lock_reset_idempotent();
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
