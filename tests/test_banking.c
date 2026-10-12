/* Public-API banking, echo RAM and OAM DMA source cases (Plan 10-12; D-15, D-16, D-17, D-19).
 *
 * Every case builds a tiny original guest, runs it through gbb_run on the DMG profile, the CGB
 * profile in CGB mode ($143 = $80) and the CGB profile in compatibility mode ($143 = $00), and
 * reads the result back from HRAM or from the work RAM copy of OAM the guest leaves at C100. The
 * expected values are derived here from the ROM image bytes or the guest's own write pattern, never
 * from the core, so a core that returned the wrong bank cannot make its own expectation.
 *
 * The same source is built a second time against two source-level core mutants (see
 * tests/CMakeLists.txt): one whose echo range F000-FDFF ignores SVBK, one whose CGB OAM DMA ignores
 * SVBK for D000-DFFF. Each mutant must fail its named case and still pass an unrelated one.
 *
 * Usage: test_banking <case> */
#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("ok 1 - %s\n", name); } while (0)

extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);

typedef enum { V_DMG = 0, V_CGB, V_COMPAT, V_COUNT } view;
static const char *const view_names[V_COUNT] = { "DMG", "CGB", "COMPAT" };

#define ROM_SIZE 65536u   /* four 16 KiB banks: an MBC5 image with ROM code 1 */
#define OAM_COPY 0xC100u  /* where the guest parks FE00-FE9F once the transfer is over */
#define BUDGET 400000u

/* MBC5 header values used here. */
#define T_ROM_ONLY 0x19u  /* MBC5 without RAM: the 64 KiB image needs a banked mapper */
#define T_MBC5_RAM 0x1Au
#define RAM_NONE 0x00u
#define RAM_8K 0x02u

/* ---- ROM image: header, bank patterns --------------------------------------------------------
 * Bank n carries pattern_byte(n, i) at offsets 0..$9F, which is exactly the window a page-aligned
 * OAM DMA reads from the start of a 16 KiB bank. */
static uint8_t pattern_byte(unsigned bank, unsigned i) {
    return (uint8_t)(0x31u + bank * 0x40u + i * 3u);
}

static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}

/* ---- tiny assembler --------------------------------------------------------------------------- */
typedef struct { uint8_t b[700]; size_t n; } prog;
static void emit(prog *p, uint8_t x) { p->b[p->n++] = x; }
static void ld_a(prog *p, uint8_t v) { emit(p, 0x3E); emit(p, v); }
static void ldh_st(prog *p, uint8_t lo) { emit(p, 0xE0); emit(p, lo); }
static void st_abs(prog *p, uint16_t a) { emit(p, 0xEA); emit(p, (uint8_t)a); emit(p, (uint8_t)(a >> 8)); }
static void ld_abs(prog *p, uint16_t a) { emit(p, 0xFA); emit(p, (uint8_t)a); emit(p, (uint8_t)(a >> 8)); }
static void write_io(prog *p, uint8_t lo, uint8_t v) { ld_a(p, v); ldh_st(p, lo); }
/* Store a constant at an absolute address. */
static void poke(prog *p, uint16_t a, uint8_t v) { ld_a(p, v); st_abs(p, a); }
/* Read an absolute address into HRAM slot `slot` (FF80 + slot). */
static void keep_abs(prog *p, uint16_t a, uint8_t slot) { ld_abs(p, a); ldh_st(p, (uint8_t)(0x80u + slot)); }
static void keep_io(prog *p, uint8_t lo, uint8_t slot) {
    emit(p, 0xF0); emit(p, lo); ldh_st(p, (uint8_t)(0x80u + slot));
}
/* Write base, base+1, ... to 160 consecutive bytes from `addr`. */
static void fill160(prog *p, uint16_t addr, uint8_t base) {
    emit(p, 0x21); emit(p, (uint8_t)addr); emit(p, (uint8_t)(addr >> 8)); /* LD HL,addr */
    emit(p, 0x06); emit(p, 0xA0);                                         /* LD B,160 */
    ld_a(p, base);
    emit(p, 0x22); emit(p, 0x3C); emit(p, 0x05); emit(p, 0x20); emit(p, 0xFB); /* LD (HL+),A; INC A; DEC B; JR NZ */
}
/* Install a routine at FF80 byte by byte. */
static void install_hram(prog *p, const uint8_t *code, size_t n) {
    for (size_t i = 0; i < n; ++i) { ld_a(p, code[i]); ldh_st(p, (uint8_t)(0x80u + i)); }
}
static void call_ff80(prog *p) { emit(p, 0xCD); emit(p, 0x80); emit(p, 0xFF); }
/* Copy FE00-FE9F to C100-C19F. */
static void park_oam(prog *p) {
    emit(p, 0x21); emit(p, 0x00); emit(p, 0xFE);                          /* LD HL,FE00 */
    emit(p, 0x11); emit(p, (uint8_t)OAM_COPY); emit(p, (uint8_t)(OAM_COPY >> 8)); /* LD DE,C100 */
    emit(p, 0x06); emit(p, 0xA0);
    emit(p, 0x2A); emit(p, 0x12); emit(p, 0x13); emit(p, 0x05); emit(p, 0x20); emit(p, 0xFA);
}
static void halt(prog *p) { emit(p, 0x76); }

/* Standard OAM DMA routine: start the transfer, then burn 176 M-cycles (a transfer is 160). */
static size_t dma_routine(uint8_t page, uint8_t *out) {
    static const uint8_t tail[] = { 0xE0, 0x46, 0x3E, 0x2C, 0x3D, 0x20, 0xFD, 0xC9 };
    out[0] = 0x3E; out[1] = page;
    memcpy(out + 2, tail, sizeof(tail));
    return 2u + sizeof(tail);
}

/* ---- machine construction and run --------------------------------------------------------------- */
static gbb_instance *load_image(view v, uint8_t type, uint8_t ram_code, const prog *p) {
    uint8_t *rom = calloc(1, ROM_SIZE);
    gbb_instance *machine = NULL;
    if (rom == NULL) return NULL;
    for (unsigned bank = 0; bank < ROM_SIZE / 0x4000u; ++bank)
        for (unsigned i = 0; i < 0xA0u; ++i) rom[bank * 0x4000u + i] = pattern_byte(bank, i);
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    memcpy(rom + 0x150, p->b, p->n);
    rom[0x143] = v == V_CGB ? 0x80 : 0x00;
    rom[0x147] = type;
    rom[0x148] = 0x01; /* 64 KiB */
    rom[0x149] = ram_code;
    fix_checksum(rom);
    if (gbb_create(v == V_DMG ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, ROM_SIZE) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

/* Run in bounded slices until the guest halts. Any stop other than an idle halt is a failure; the
 * UNSUPPORTED_BUS stop in particular would mean a guest access the core refused. */
static int run_to_halt(gbb_instance *m) {
    for (int slice = 0; slice < 8; ++slice) {
        const gbb_run_result r = gbb_run(m, BUDGET, NULL, 0);
        if (r.reason == GBB_STOP_HALTED_IDLE) return 1;
        if (r.reason != GBB_STOP_BUDGET) return 0;
    }
    return 0;
}

static uint8_t hram(const gbb_instance *m, unsigned slot) { return gbb_peek_ram(m, (uint16_t)(0xFF80u + slot)); }

/* A DMA experiment: `pre` is the guest setup, then the standard routine for `page` runs, then the
 * guest parks OAM at C100. Returns the machine (still alive) or NULL on a harness failure. */
static gbb_instance *run_dma(view v, uint8_t type, uint8_t ram_code, const prog *pre, uint8_t page) {
    prog p = { {0}, 0 };
    write_io(&p, 0x40, 0x00); /* LCD off: VRAM and OAM are always reachable */
    memcpy(p.b + p.n, pre->b, pre->n);
    p.n += pre->n;
    uint8_t routine[16];
    const size_t rn = dma_routine(page, routine);
    install_hram(&p, routine, rn);
    call_ff80(&p);
    park_oam(&p);
    halt(&p);
    gbb_instance *m = load_image(v, type, ram_code, &p);
    if (m == NULL) return NULL;
    if (!run_to_halt(m)) { gbb_destroy(m); return NULL; }
    return m;
}

static int oam_is_pattern(const gbb_instance *m, uint8_t base) {
    for (unsigned i = 0; i < 160u; ++i)
        if (gbb_peek_ram(m, (uint16_t)(OAM_COPY + i)) != (uint8_t)(base + i)) return 0;
    return 1;
}
static int oam_is_constant(const gbb_instance *m, uint8_t value) {
    for (unsigned i = 0; i < 160u; ++i)
        if (gbb_peek_ram(m, (uint16_t)(OAM_COPY + i)) != value) return 0;
    return 1;
}
static int oam_is_rom(const gbb_instance *m, unsigned bank) {
    for (unsigned i = 0; i < 160u; ++i)
        if (gbb_peek_ram(m, (uint16_t)(OAM_COPY + i)) != pattern_byte(bank, i)) return 0;
    return 1;
}

/* Guest setup for the WRAM DMA experiment: bank 2 holds $20+i, bank 3 holds $30+i, and the bank the
 * transfer runs under is `final_bank`. */
static void wram_pattern_pre(prog *p, uint8_t final_bank) {
    write_io(p, 0x70, 0x02); fill160(p, 0xD000, 0x20);
    write_io(p, 0x70, 0x03); fill160(p, 0xD000, 0x30);
    write_io(p, 0x70, final_bank);
}

/* ---- tracer ------------------------------------------------------------------------------------ */
static int case_dma_wram_bank(void) {
    prog pre = { {0}, 0 };
    wram_pattern_pre(&pre, 0x02);
    gbb_instance *m = run_dma(V_CGB, T_ROM_ONLY, RAM_NONE, &pre, 0xD0);
    REQUIRE(m != NULL);
    REQUIRE(oam_is_pattern(m, 0x20));       /* the bank-2 bytes, not the later bank-3 ones */
    uint8_t vb = 9, wb = 9;
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(wb == 2);
    gbb_destroy(m);

    /* The same bytes reached under bank 3 give the other pattern, so the page follows SVBK. */
    prog pre3 = { {0}, 0 };
    wram_pattern_pre(&pre3, 0x03);
    m = run_dma(V_CGB, T_ROM_ONLY, RAM_NONE, &pre3, 0xD0);
    REQUIRE(m != NULL);
    REQUIRE(oam_is_pattern(m, 0x30));
    gbb_destroy(m);

    /* C0 is the fixed bank: the same experiment on page C0 sees bank 0 whatever SVBK says. */
    prog prec = { {0}, 0 };
    fill160(&prec, 0xC000, 0x90);
    write_io(&prec, 0x70, 0x05);
    m = run_dma(V_CGB, T_ROM_ONLY, RAM_NONE, &prec, 0xC0);
    REQUIRE(m != NULL);
    REQUIRE(oam_is_pattern(m, 0x90));
    gbb_destroy(m);
    PASS("banking_dma_wram_bank");
    return 0;
}

/* ---- banks and echo through the CPU bus ---------------------------------------------------------- */
static gbb_instance *run_plain(view v, const prog *body) {
    prog p = { {0}, 0 };
    write_io(&p, 0x40, 0x00);
    memcpy(p.b + p.n, body->b, body->n);
    p.n += body->n;
    halt(&p);
    gbb_instance *m = load_image(v, T_ROM_ONLY, RAM_NONE, &p);
    if (m == NULL) return NULL;
    if (!run_to_halt(m)) { gbb_destroy(m); return NULL; }
    return m;
}

static int case_vbk_independence(void) {
    prog b = { {0}, 0 };
    write_io(&b, 0x4F, 0x00);
    poke(&b, 0x8000, 0x11); poke(&b, 0x9800, 0x12);
    write_io(&b, 0x4F, 0x01);
    poke(&b, 0x8000, 0x21); poke(&b, 0x9800, 0x22);
    keep_io(&b, 0x4F, 0);                       /* $FE | 1 */
    keep_abs(&b, 0x8000, 1); keep_abs(&b, 0x9800, 2);
    write_io(&b, 0x4F, 0x00);
    keep_io(&b, 0x4F, 3);                       /* $FE | 0 */
    keep_abs(&b, 0x8000, 4); keep_abs(&b, 0x9800, 5);
    gbb_instance *m = run_plain(V_CGB, &b);
    REQUIRE(m != NULL);
    REQUIRE(hram(m, 0) == 0xFF && hram(m, 3) == 0xFE);
    REQUIRE(hram(m, 1) == 0x21 && hram(m, 2) == 0x22);   /* bank 1 kept its own bytes */
    REQUIRE(hram(m, 4) == 0x11 && hram(m, 5) == 0x12);   /* bank 0 kept its own bytes */
    gbb_destroy(m);

    /* Compatibility mode: the VBK write is ignored, there is one bank, and the second write wins. */
    prog c = { {0}, 0 };
    poke(&c, 0x8000, 0x11);
    write_io(&c, 0x4F, 0x01);
    keep_io(&c, 0x4F, 0);
    poke(&c, 0x8000, 0x21);
    write_io(&c, 0x4F, 0x00);
    keep_abs(&c, 0x8000, 1);
    m = run_plain(V_COMPAT, &c);
    REQUIRE(m != NULL);
    REQUIRE(hram(m, 0) == 0xFE);
    REQUIRE(hram(m, 1) == 0x21);
    uint8_t vb = 9, wb = 9;
    gbb_test_bank_state(m, &vb, &wb);
    REQUIRE(vb == 0);
    gbb_destroy(m);
    PASS("banking_vbk_independence");
    return 0;
}

static int case_svbk_readback(void) {
    prog b = { {0}, 0 };
    for (unsigned k = 0; k < 8u; ++k) {
        write_io(&b, 0x70, (uint8_t)k);
        keep_io(&b, 0x70, (uint8_t)k);
        poke(&b, 0xD000, (uint8_t)(0xA0u + k));
    }
    for (unsigned k = 0; k < 8u; ++k) {
        write_io(&b, 0x70, (uint8_t)k);
        keep_abs(&b, 0xD000, (uint8_t)(8u + k));
    }
    gbb_instance *m = run_plain(V_CGB, &b);
    REQUIRE(m != NULL);
    for (unsigned k = 0; k < 8u; ++k) {
        REQUIRE(hram(m, k) == (uint8_t)(0xF8u | k));
        /* Bank 0 selects bank 1, so the marker written for 0 is overwritten by the one for 1. */
        const uint8_t expected = k <= 1u ? 0xA1u : (uint8_t)(0xA0u + k);
        REQUIRE(hram(m, 8u + k) == expected);
    }
    gbb_destroy(m);
    PASS("banking_svbk_readback");
    return 0;
}

static int case_echo_follows_bank(void) {
    prog b = { {0}, 0 };
    poke(&b, 0xC000, 0xC0); poke(&b, 0xC001, 0xC1); poke(&b, 0xCFFF, 0xCF);
    /* Slots per bank k: D000, D001, DDFF as written through F000, F001, FDFF, then E000, E001, EFFF. */
    for (unsigned k = 0; k < 8u; ++k) {
        const uint8_t s = (uint8_t)(k * 6u);
        write_io(&b, 0x70, (uint8_t)k);
        poke(&b, 0xF000, (uint8_t)(0x10u + k));
        poke(&b, 0xF001, (uint8_t)(0x20u + k));
        poke(&b, 0xFDFF, (uint8_t)(0x30u + k));
        keep_abs(&b, 0xD000, s); keep_abs(&b, 0xD001, (uint8_t)(s + 1u)); keep_abs(&b, 0xDDFF, (uint8_t)(s + 2u));
        keep_abs(&b, 0xE000, (uint8_t)(s + 3u)); keep_abs(&b, 0xE001, (uint8_t)(s + 4u));
        keep_abs(&b, 0xEFFF, (uint8_t)(s + 5u));
    }
    /* Reverse direction under one bank: a store through D000 is read back through F000. */
    write_io(&b, 0x70, 0x06);
    poke(&b, 0xD123, 0x5C);
    keep_abs(&b, 0xF123, 48);
    keep_abs(&b, 0xE123, 49);   /* E123 mirrors C123, which was never written */
    gbb_instance *m = run_plain(V_CGB, &b);
    REQUIRE(m != NULL);
    int echo_reads_match = 1;
    for (unsigned k = 0; k < 8u; ++k) {
        const unsigned s = k * 6u;
        if (hram(m, s) != (uint8_t)(0x10u + k)) echo_reads_match = 0;       /* F000 -> D000 under bank k */
        if (hram(m, s + 1u) != (uint8_t)(0x20u + k)) echo_reads_match = 0;
        if (hram(m, s + 2u) != (uint8_t)(0x30u + k)) echo_reads_match = 0;  /* FDFF -> DDFF */
    }
    int fixed_half_ok = 1;
    for (unsigned k = 0; k < 8u; ++k) {
        const unsigned s = k * 6u;
        if (hram(m, s + 3u) != 0xC0 || hram(m, s + 4u) != 0xC1 || hram(m, s + 5u) != 0xCF) fixed_half_ok = 0;
    }
    REQUIRE(fixed_half_ok);      /* E000-EFFF mirrors C000-CFFF under every SVBK */
    REQUIRE(echo_reads_match);   /* F000-FDFF mirrors D000-DDFF of the selected bank */
    REQUIRE(hram(m, 48) == 0x5C);
    REQUIRE(hram(m, 49) == 0x00);
    gbb_destroy(m);
    PASS("banking_echo_follows_bank");
    return 0;
}

/* ---- OAM DMA sources --------------------------------------------------------------------------- */
static int case_dma_vram_bank(void) {
    for (unsigned vbk = 0; vbk < 2u; ++vbk) {
        prog pre = { {0}, 0 };
        write_io(&pre, 0x4F, 0x00); fill160(&pre, 0x8000, 0x10);
        write_io(&pre, 0x4F, 0x01); fill160(&pre, 0x8000, 0x80);
        write_io(&pre, 0x4F, (uint8_t)vbk);
        gbb_instance *m = run_dma(V_CGB, T_ROM_ONLY, RAM_NONE, &pre, 0x80);
        REQUIRE(m != NULL);
        REQUIRE(oam_is_pattern(m, vbk == 0u ? 0x10 : 0x80));
        gbb_destroy(m);
    }
    PASS("banking_dma_vram_bank");
    return 0;
}

static int case_dma_rom_page(void) {
    const prog none = { {0}, 0 };
    for (view v = V_DMG; v < V_COUNT; ++v) {
        gbb_instance *m = run_dma(v, T_MBC5_RAM, RAM_8K, &none, 0x00);
        REQUIRE(m != NULL);
        if (v == V_DMG) REQUIRE(oam_is_constant(m, 0xFF));  /* D-024: ROM pages read $FF on the DMG profile */
        else REQUIRE(oam_is_rom(m, 0));
        gbb_destroy(m);
    }
    /* The switchable window follows the mapper: bank 2 selected, page 40 reads bank 2. */
    prog sel = { {0}, 0 };
    poke(&sel, 0x2000, 0x02);
    for (view v = V_DMG; v < V_COUNT; ++v) {
        gbb_instance *m = run_dma(v, T_MBC5_RAM, RAM_8K, &sel, 0x40);
        REQUIRE(m != NULL);
        if (v == V_DMG) REQUIRE(oam_is_constant(m, 0xFF));
        else REQUIRE(oam_is_rom(m, 2));
        gbb_destroy(m);
    }
    PASS("banking_dma_rom_page");
    return 0;
}

static int case_dma_high_pages(void) {
    static const uint8_t pages[] = { 0xE0, 0xF0, 0xFE, 0xFF };
    const prog none = { {0}, 0 };
    for (view v = V_DMG; v < V_COUNT; ++v) {
        for (size_t i = 0; i < sizeof(pages); ++i) {
            gbb_instance *m = run_dma(v, T_ROM_ONLY, RAM_NONE, &none, pages[i]);
            if (m == NULL) { fprintf(stderr, "harness failure %s page %02X\n", view_names[v], pages[i]); return 1; }
            REQUIRE(oam_is_constant(m, 0xFF));
            gbb_destroy(m);
        }
    }
    PASS("banking_dma_high_pages");
    return 0;
}

static int case_dma_cart_ram(void) {
    prog on = { {0}, 0 };
    poke(&on, 0x0000, 0x0A);          /* RAM enable */
    fill160(&on, 0xA000, 0x50);
    for (view v = V_DMG; v < V_COUNT; ++v) {
        gbb_instance *m = run_dma(v, T_MBC5_RAM, RAM_8K, &on, 0xA0);
        REQUIRE(m != NULL);
        if (v == V_DMG) REQUIRE(oam_is_constant(m, 0xFF));
        else REQUIRE(oam_is_pattern(m, 0x50));
        gbb_destroy(m);
    }
    /* Negative control: with RAM disabled again the cartridge returns $FF, so a DMA that bypassed the
     * mapper and read the RAM buffer directly would still see the pattern. */
    prog off = { {0}, 0 };
    memcpy(off.b, on.b, on.n); off.n = on.n;
    poke(&off, 0x0000, 0x00);
    gbb_instance *m = run_dma(V_CGB, T_MBC5_RAM, RAM_8K, &off, 0xA0);
    REQUIRE(m != NULL);
    REQUIRE(oam_is_constant(m, 0xFF));
    gbb_destroy(m);
    PASS("banking_dma_cart_ram");
    return 0;
}

static int case_dmg_banks_frozen(void) {
    /* CPU view: both bank registers are accepted writes with no effect, so a second store to the
     * same address overwrites the first on the DMG profile and on a compatibility-mode CGB. */
    for (view v = V_DMG; v < V_COUNT; ++v) {
        if (v == V_CGB) continue;
        prog b = { {0}, 0 };
        write_io(&b, 0x70, 0x03); poke(&b, 0xD000, 0x5A);
        write_io(&b, 0x70, 0x05); poke(&b, 0xD000, 0x6B);
        keep_abs(&b, 0xD000, 0);
        keep_abs(&b, 0xF000, 1);      /* the echo shows the same single bank */
        write_io(&b, 0x4F, 0x01); poke(&b, 0x8000, 0x77);
        write_io(&b, 0x4F, 0x00); poke(&b, 0x8000, 0x88);
        keep_abs(&b, 0x8000, 2);
        gbb_instance *m = run_plain(v, &b);
        if (m == NULL) { fprintf(stderr, "harness failure %s\n", view_names[v]); return 1; }
        REQUIRE(hram(m, 0) == 0x6B && hram(m, 1) == 0x6B);
        REQUIRE(hram(m, 2) == 0x88);
        uint8_t vb = 9, wb = 9;
        gbb_test_bank_state(m, &vb, &wb);
        REQUIRE(vb == 0 && wb == 1);
        gbb_destroy(m);

        /* DMA view: the same two fills land in one place, so the later one is what the transfer sees. */
        prog pre = { {0}, 0 };
        wram_pattern_pre(&pre, 0x02);
        m = run_dma(v, T_ROM_ONLY, RAM_NONE, &pre, 0xD0);
        REQUIRE(m != NULL);
        REQUIRE(oam_is_pattern(m, 0x30));
        gbb_destroy(m);
        prog vpre = { {0}, 0 };
        write_io(&vpre, 0x4F, 0x00); fill160(&vpre, 0x8000, 0x10);
        write_io(&vpre, 0x4F, 0x01); fill160(&vpre, 0x8000, 0x80);
        write_io(&vpre, 0x4F, 0x00);
        m = run_dma(v, T_ROM_ONLY, RAM_NONE, &vpre, 0x80);
        REQUIRE(m != NULL);
        REQUIRE(oam_is_pattern(m, 0x80));
        gbb_destroy(m);
    }
    PASS("banking_dmg_banks_frozen");
    return 0;
}

/* D-17: the DMG "only HRAM during OAM DMA" CPU rule is kept on the CGB profile although real CGB
 * hardware uses separate buses (expected-failure:cgb-separate-buses, GATE-16 and GATE-25). This
 * pins today's behaviour so changing it is a deliberate edit of this case, the gate rows and the
 * limitation in docs/cgb-profile.md. The same guest on the DMG profile is the control. */
static int bus_conflict_values(view v, uint8_t *read_value, uint8_t *c000_after) {
    prog p = { {0}, 0 };
    write_io(&p, 0x40, 0x00);
    poke(&p, 0xC000, 0x5A);
    static const uint8_t routine[] = {
        0x3E, 0xC0, 0xE0, 0x46,        /* LD A,C0; LDH (46),A: DMA from WRAM */
        0x01, 0x00, 0xC0,              /* LD BC,C000 */
        0x0A,                          /* LD A,(BC): a CPU read of WRAM while the transfer runs */
        0xE0, 0xB0,                    /* LDH (B0),A: HRAM is the one region the rule allows */
        0x3E, 0x77, 0x02,              /* LD A,77; LD (BC),A: a CPU write to WRAM, dropped by the rule */
        0x3E, 0x2C, 0x3D, 0x20, 0xFD,  /* wait out the transfer */
        0xC9 };
    install_hram(&p, routine, sizeof(routine));
    call_ff80(&p);
    halt(&p);
    gbb_instance *m = load_image(v, T_ROM_ONLY, RAM_NONE, &p);
    if (m == NULL) return 0;
    if (!run_to_halt(m)) { gbb_destroy(m); return 0; }
    *read_value = gbb_peek_ram(m, 0xFFB0u);
    *c000_after = gbb_peek_ram(m, 0xC000u);
    gbb_destroy(m);
    return 1;
}

static int case_bus_conflict_cgb_pin(void) {
    uint8_t dmg_read = 0, dmg_c000 = 0, cgb_read = 0, cgb_c000 = 0, compat_read = 0, compat_c000 = 0;
    REQUIRE(bus_conflict_values(V_DMG, &dmg_read, &dmg_c000));
    REQUIRE(bus_conflict_values(V_CGB, &cgb_read, &cgb_c000));
    REQUIRE(bus_conflict_values(V_COMPAT, &compat_read, &compat_c000));
    /* The DMG rule: the read returns $FF and the write is dropped, so C000 keeps $5A. */
    REQUIRE(dmg_read == 0xFF && dmg_c000 == 0x5A);
    REQUIRE(cgb_read == dmg_read && cgb_c000 == dmg_c000);
    REQUIRE(compat_read == dmg_read && compat_c000 == dmg_c000);
    PASS("banking_bus_conflict_cgb_pin");
    return 0;
}

/* ---- Original fixture guests (fixtures/cgb-banking, Plan 10-13; D-18) ---------------------------
 * The committed ROMs are original project work built from one source (see the fixture manifest).
 * The guest chooses its expectations from its own $0143 byte and the entry A register, and leaves
 * C000 = $A5 pass / $EE fail, C001 = run kind and one result byte per cell from C002
 * ($01 pass, $FF fail, $00 not run). Every expectation below is written from the protocol, never
 * read back from the core. */
#define GUEST_MAX_BYTES 32768u
#define GUEST_BUDGET 2000000u   /* the manifest protocol timeout, in half dots */
#define GUEST_CELLS 9u          /* C002..C00A */

typedef struct { uint8_t verdict, kind, cell[GUEST_CELLS]; } guest_result;

static uint8_t *read_guest_rom(const char *dir, const char *name, size_t *size) {
    char path[1024];
    if (snprintf(path, sizeof(path), "%s/%s", dir, name) >= (int)sizeof(path)) return NULL;
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    uint8_t *rom = malloc(GUEST_MAX_BYTES + 1u);
    if (rom == NULL) { fclose(f); return NULL; }
    *size = fread(rom, 1u, GUEST_MAX_BYTES + 1u, f);
    fclose(f);
    if (*size != GUEST_MAX_BYTES) { free(rom); return NULL; } /* the committed guests are exactly 32 KiB */
    return rom;
}

/* Run the image to its final HALT on `profile` and collect the result bytes. */
static int run_guest(uint8_t *rom, size_t size, gbb_profile profile, guest_result *out) {
    gbb_instance *m = NULL;
    fix_checksum(rom);
    if (gbb_create(profile, &m) != GBB_OK) return 0;
    if (gbb_load_rom(m, rom, size) != GBB_OK) { gbb_destroy(m); return 0; }
    const gbb_run_result r = gbb_run(m, GUEST_BUDGET, NULL, 0);
    int ok = r.reason == GBB_STOP_HALTED_IDLE;
    out->verdict = gbb_peek_ram(m, 0xC000u);
    out->kind = gbb_peek_ram(m, 0xC001u);
    for (unsigned i = 0; i < GUEST_CELLS; ++i) out->cell[i] = gbb_peek_ram(m, (uint16_t)(0xC002u + i));
    gbb_destroy(m);
    return ok;
}

/* Cell result bytes, in C002 order. */
enum { CELL_VBK = 0, CELL_SVBK, CELL_ECHO_BANK, CELL_ECHO_MIRROR, CELL_DMA_WRAM, CELL_DMA_VRAM,
       CELL_DMA_HIGH, CELL_DMA_ROM, CELL_FROZEN };

static int guest_dir_case(const char *dir, const char *name, gbb_profile profile,
                          uint8_t cgb_flag, guest_result *r) {
    size_t size = 0;
    uint8_t *rom = read_guest_rom(dir, name, &size);
    if (rom == NULL) return 0;
    const int header_ok = rom[0x143] == cgb_flag && rom[0x147] == 0x00 && rom[0x148] == 0x00;
    const int ran = header_ok && run_guest(rom, size, profile, r);
    free(rom);
    return ran;
}

static int case_cgb_banking_guest_cgb(const char *dir) {
    guest_result r;
    REQUIRE(guest_dir_case(dir, "banking-cgb.gb", GBB_PROFILE_CGB_CPU_E, 0x80, &r));
    REQUIRE(r.kind == 1);
    REQUIRE(r.cell[CELL_SVBK] == 0x01);
    REQUIRE(r.verdict == 0xA5);
    PASS("cgb_banking_guest_cgb");
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3) { /* fixture guest cases: <case> <fixture directory> */
        static const struct { const char *name; int (*fn)(const char *); } guests[] = {
            { "cgb_banking_guest_cgb", case_cgb_banking_guest_cgb },
        };
        for (size_t i = 0; i < sizeof(guests) / sizeof(guests[0]); ++i)
            if (strcmp(argv[1], guests[i].name) == 0) return guests[i].fn(argv[2]);
        fprintf(stderr, "unknown case %s\n", argv[1]);
        return 2;
    }
    if (argc != 2) {
        fprintf(stderr, "usage: test_banking <case> [fixture-dir]\n");
        return 2;
    }
    static const struct { const char *name; int (*fn)(void); } cases[] = {
        { "dma_wram_bank", case_dma_wram_bank },
        { "vbk_independence", case_vbk_independence },
        { "svbk_readback", case_svbk_readback },
        { "echo_follows_bank", case_echo_follows_bank },
        { "dma_vram_bank", case_dma_vram_bank },
        { "dma_rom_page", case_dma_rom_page },
        { "dma_high_pages", case_dma_high_pages },
        { "dma_cart_ram", case_dma_cart_ram },
        { "dmg_banks_frozen", case_dmg_banks_frozen },
        { "bus_conflict_cgb_pin", case_bus_conflict_cgb_pin },
    };
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i)
        if (strcmp(argv[1], cases[i].name) == 0) return cases[i].fn();
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
