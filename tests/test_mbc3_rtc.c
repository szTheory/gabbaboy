#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Black-box RTC tests: synthetic MBC3 images whose guest programs touch the clock
 * through the cartridge bus only. No assembled fixture, no commercial data. */

typedef struct {
    uint8_t bytes[4096];
    size_t used;
} program;

static void emit_raw(program *p, const uint8_t *b, size_t n) {
    memcpy(p->bytes + p->used, b, n);
    p->used += n;
}

static void emit_write(program *p, uint16_t address, uint8_t value) {
    const uint8_t b[] = {0x3Eu, value, 0xEAu, (uint8_t)address, (uint8_t)(address >> 8)};
    emit_raw(p, b, sizeof(b));
}

static void emit_read_to(program *p, uint16_t address, uint16_t destination) {
    const uint8_t b[] = {0xFAu, (uint8_t)address, (uint8_t)(address >> 8),
                         0xEAu, (uint8_t)destination, (uint8_t)(destination >> 8)};
    emit_raw(p, b, sizeof(b));
}

static void emit_halt(program *p) { p->bytes[p->used++] = 0x76u; }

/* Latch ($00 then $01) and copy the five latched registers to C000+first. */
static void emit_latch_and_copy(program *p, uint16_t first) {
    emit_write(p, 0x6000u, 0x00u);
    emit_write(p, 0x6000u, 0x01u);
    for (uint8_t reg = 0u; reg < 5u; ++reg) {
        emit_write(p, 0x4000u, (uint8_t)(0x08u + reg));
        emit_read_to(p, 0xA000u, (uint16_t)(first + reg));
    }
}

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* JP $0200 from the entry point; the program lives past the header. The VBlank
 * vector at $0040 is DEC B ; RETI so a guest can count frames in register B. */
static gbb_instance *load_program(uint8_t type, uint8_t ram_code, const program *p) {
    static uint8_t rom[0x8000];
    memset(rom, 0, sizeof(rom));
    rom[0x147u] = type;
    rom[0x148u] = 0x00u;
    rom[0x149u] = ram_code;
    fix_checksum(rom);
    rom[0x40u] = 0x05u; /* DEC B */
    rom[0x41u] = 0xD9u; /* RETI */
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, p->bytes, p->used);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    if (gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

/* Run a fixed emulated duration. A halted guest returns HALTED_IDLE after consuming
 * one eligible idle stretch, so progress is counted in consumed half-dots, not calls.
 * The guest programs finish well inside the duration and latched bytes do not move
 * afterwards. Returns 0 when the guest hit an illegal opcode, lockup or invalid state. */
static int run_for(gbb_instance *machine, uint64_t half_dots) {
    uint64_t done = 0u;
    while (done < half_dots) {
        const gbb_run_result run = gbb_run(machine, half_dots - done, NULL, 0u);
        if (run.reason == GBB_STOP_UNSUPPORTED_OPCODE || run.reason == GBB_STOP_INVALID_STATE ||
            run.reason == GBB_STOP_LOCKUP)
            return 0;
        /* The final HALT of a program, with nothing left to run, ends in a bus-level
         * stop; the guest has finished and the RAM results are asserted by the caller. */
        if (run.reason == GBB_STOP_UNSUPPORTED_BUS) return 1;
        done += run.consumed_half_dots;
        /* Halted with nothing able to wake it: the guest has finished. */
        if (run.reason == GBB_STOP_HALTED_IDLE && run.consumed_half_dots == 0u) return 1;
    }
    return 1;
}

/* 150 VBlanks is 21,067,200 half-dots, about 2.51 s: two whole seconds plus at most
 * one frame of slack before a third tick at 3 s. */
static int rtc_tracer(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0x4000u, 0x08u); emit_write(&p, 0xA000u, 58u);
    emit_write(&p, 0x4000u, 0x09u); emit_write(&p, 0xA000u, 59u);
    emit_write(&p, 0x4000u, 0x0Au); emit_write(&p, 0xA000u, 23u);
    emit_write(&p, 0x4000u, 0x0Bu); emit_write(&p, 0xA000u, 0xFFu);
    emit_write(&p, 0x4000u, 0x0Cu); emit_write(&p, 0xA000u, 0x01u);
    {
        /* LD A,$01 ; LDH ($FF),A ; LD B,150 ; EI ; loop: HALT ; LD A,B ; OR A ; JR NZ,loop ; DI */
        const uint8_t wait[] = {0x3Eu, 0x01u, 0xE0u, 0xFFu, 0x06u, 150u, 0xFBu,
                                0x76u, 0x78u, 0xB7u, 0x20u, 0xFBu, 0xF3u};
        emit_raw(&p, wait, sizeof(wait));
    }
    emit_latch_and_copy(&p, 0xC000u);
    emit_halt(&p);

    gbb_instance *machine = load_program(0x10u, 0x02u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_for(machine, 30000000u));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0u); /* seconds 58 + 2 -> 0 */
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0u); /* minutes 59 + 1 -> 0 */
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0u); /* hours 23 + 1 -> 0 */
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0u); /* day 511 + 1 -> 0 */
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0x80u); /* sticky day carry, running */
    gbb_destroy(machine);
    return 0;
}

static int rtc_gate_and_select(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x4000u, 0x08u);
    emit_write(&p, 0xA000u, 0x05u);        /* RAMG closed: ignored */
    emit_read_to(&p, 0xA000u, 0xC000u);    /* closed: $FF */
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA000u, 21u);
    emit_write(&p, 0x6000u, 0x00u);
    emit_write(&p, 0x6000u, 0x01u);
    emit_read_to(&p, 0xA000u, 0xC001u);    /* seconds 21 */
    emit_write(&p, 0x4000u, 0x09u);        /* a new selection replaces the old one */
    emit_read_to(&p, 0xA000u, 0xC002u);    /* minutes 0 */
    emit_write(&p, 0x0000u, 0x00u);
    emit_read_to(&p, 0xA000u, 0xC003u);    /* closed again: $FF */
    emit_write(&p, 0x0000u, 0xFAu);        /* (v & 0x0F) == 0x0A opens the gate */
    emit_read_to(&p, 0xA000u, 0xC004u);
    emit_halt(&p);
    gbb_instance *machine = load_program(0x10u, 0x02u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_for(machine, 2000000u));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 21u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0u);
    gbb_destroy(machine);

    /* $0F has a timer and battery but RAM code $00: the clock still works. */
    program q = {{0}, 0u};
    emit_write(&q, 0x0000u, 0x0Au);
    emit_write(&q, 0x4000u, 0x08u);
    emit_write(&q, 0xA000u, 7u);
    emit_write(&q, 0x6000u, 0x00u);
    emit_write(&q, 0x6000u, 0x01u);
    emit_read_to(&q, 0xA000u, 0xC000u);
    emit_write(&q, 0x4000u, 0x00u);
    emit_read_to(&q, 0xA000u, 0xC001u);    /* no RAM behind selection 0 */
    emit_halt(&q);
    machine = load_program(0x0Fu, 0x00u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(run_for(machine, 2000000u));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 7u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    gbb_destroy(machine);
    return 0;
}

static int rtc_load_fresh(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_latch_and_copy(&p, 0xC000u);
    emit_halt(&p);
    gbb_instance *machine = load_program(0x10u, 0x02u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_for(machine, 2000000u));
    for (uint16_t i = 0u; i < 5u; ++i)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + i)) == 0u);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "rtc_tracer") == 0) return rtc_tracer();
    if (strcmp(argv[1], "rtc_gate_and_select") == 0) return rtc_gate_and_select();
    if (strcmp(argv[1], "rtc_load_fresh") == 0) return rtc_load_fresh();
    return 2;
}
