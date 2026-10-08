#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WIDTH 160u
#define HEIGHT 144u
#define PIXELS (WIDTH * HEIGHT)
static const char *active_case = "unknown";
#define REQUIRE(x) do { if (!(x)) { \
    printf("TAP version 13\n1..1\nnot ok 1 - %s\n  ---\n  message: \"assertion at line %d: %s\"\n  ...\n", active_case, __LINE__, #x); return 1; \
} } while (0)

typedef struct {
    uint8_t bytes[4096];
    size_t size;
} small_program;

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_dma_event;

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

extern void gbb_test_dma_observer_set(gbb_instance *, gbb_test_dma_event *, size_t);
extern size_t gbb_test_dma_observer_count(const gbb_instance *);
extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);
extern void gbb_test_ppu_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_ppu_observer_count(const gbb_instance *);

static void emit(small_program *p, uint8_t value) {
    if (p->size < sizeof(p->bytes)) p->bytes[p->size++] = value;
}

static void emit16(small_program *p, uint16_t value) {
    emit(p, (uint8_t)value);
    emit(p, (uint8_t)(value >> 8));
}

static void emit_memory_byte(small_program *p, uint16_t address, uint8_t value) {
    emit(p, 0x21); emit16(p, address);       /* LD HL,address */
    emit(p, 0x3E); emit(p, value);           /* LD A,value */
    emit(p, 0x22);                           /* LD [HL+],A */
}

static void emit_source_record(small_program *p, uint16_t address, uint8_t y) {
    emit_memory_byte(p, address, y);
    emit_memory_byte(p, (uint16_t)(address + 1u), 8u);
    emit_memory_byte(p, (uint16_t)(address + 2u), 0u);
    emit_memory_byte(p, (uint16_t)(address + 3u), 0u);
}

static void emit_copy_to_hram(small_program *p, uint16_t *source_address,
                              const uint8_t *routine, size_t routine_size) {
    emit(p, 0x21);                           /* LD HL,routine bytes */
    size_t source_operand = p->size;
    emit16(p, 0);
    emit(p, 0x11); emit16(p, 0xFF80);       /* LD DE,FF80 */
    emit(p, 0x06); emit(p, (uint8_t)routine_size); /* LD B,size */
    size_t loop = p->size;
    emit(p, 0x2A);                           /* LD A,[HL+] */
    emit(p, 0x12);                           /* LD [DE],A */
    emit(p, 0x13);                           /* INC DE */
    emit(p, 0x05);                           /* DEC B */
    emit(p, 0x20);
    size_t relative_operand = p->size;
    emit(p, 0);
    int displacement = (int)loop - (int)(relative_operand + 1u);
    p->bytes[relative_operand] = (uint8_t)displacement;
    emit(p, 0xC3); emit16(p, 0xFF80);       /* JP FF80 */
    *source_address = (uint16_t)(0x0150u + p->size);
    p->bytes[source_operand] = (uint8_t)*source_address;
    p->bytes[source_operand + 1u] = (uint8_t)(*source_address >> 8);
    for (size_t i = 0; i < routine_size; ++i) emit(p, routine[i]);
}

static gbb_instance *load_dma_guest(uint8_t source_page, int restart,
                                    int probe_cpu_access, int boundary_probe,
                                    int interrupt_probe) {
    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;

    small_program main_program = {{0}, 0};
    emit(&main_program, 0xAF);              /* XOR A */
    emit(&main_program, 0xE0); emit(&main_program, 0x40); /* LCD off */
    emit_source_record(&main_program, 0x8000, 16u); /* tile 0 and optional DMA source */
    if (source_page != 0x80u)
        emit_source_record(&main_program, (uint16_t)((uint16_t)source_page << 8), 16u);
    if (restart)
        emit_source_record(&main_program, 0xD000, 1u); /* replacement would hide OBJ 0 */
    if (interrupt_probe) {
        emit(&main_program, 0x31); emit16(&main_program, 0xC002); /* SP=C002 */
        emit(&main_program, 0x3E); emit(&main_program, 1u);
        emit(&main_program, 0xE0); emit(&main_program, 0x0F); /* pending VBlank */
        emit(&main_program, 0xEA); emit16(&main_program, 0xFFFF); /* enable VBlank */
    }

    uint8_t routine[64];
    size_t routine_size = 0;
    routine[routine_size++] = 0x3E; routine[routine_size++] = source_page;
    if (interrupt_probe) routine[routine_size++] = 0xFB; /* EI, then FF46 */
    routine[routine_size++] = 0xE0; routine[routine_size++] = 0x46;
    if (restart) {
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0xD0;
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0x46;
    }
    if (probe_cpu_access) {
        routine[routine_size++] = 0x01; routine[routine_size++] = 0x00;
        routine[routine_size++] = 0xC0; /* LD BC,C000 */
        routine[routine_size++] = 0x0A;  /* blocked CPU read -> A */
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0xB0;
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0x77;
        routine[routine_size++] = 0x02;  /* blocked CPU write to C000 */
        routine[routine_size++] = 0x21; routine[routine_size++] = 0x00;
        routine[routine_size++] = 0x80; /* LD HL,8000 */
        routine[routine_size++] = 0x7E;  /* blocked VRAM read -> FF */
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0xB1;
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0x77;
        routine[routine_size++] = 0x77;  /* blocked VRAM write */
        routine[routine_size++] = 0x21; routine[routine_size++] = 0x00;
        routine[routine_size++] = 0xFE; /* LD HL,FE00 */
        routine[routine_size++] = 0x7E;  /* blocked OAM read -> FF */
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0xB2;
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0x77;
        routine[routine_size++] = 0x77;  /* blocked OAM write */
    }
    if (boundary_probe) {
        routine[routine_size++] = 0x21; routine[routine_size++] = 0x00;
        routine[routine_size++] = boundary_probe == 2 ? 0xFE : 0xC0;
        routine[routine_size++] = 0x06; routine[routine_size++] = 0x25;
        routine[routine_size++] = 0x05; /* 37-cycle loop and six NOPs */
        routine[routine_size++] = 0x20; routine[routine_size++] = 0xFD;
        for (unsigned i = 0; i < 6; ++i) routine[routine_size++] = 0x00;
        routine[routine_size++] = boundary_probe == 2 ? 0x7E : 0x2A;
        routine[routine_size++] = boundary_probe == 2 ? 0x7E : 0x2A;
        routine[routine_size++] = boundary_probe == 2 ? 0x7E : 0x2A;
    } else {
        routine[routine_size++] = 0x06; routine[routine_size++] = 0x28; /* 40 M-cycles */
        routine[routine_size++] = 0x05;      /* DEC B */
        routine[routine_size++] = 0x20;
        routine[routine_size++] = 0xFD;      /* JR NZ,DEC B */
        routine[routine_size++] = 0x00;      /* two M-cycles past nominal end */
        routine[routine_size++] = 0x00;
    }
    routine[routine_size++] = 0xC3; routine[routine_size++] = 0x00;
    routine[routine_size++] = 0x02;      /* JP 0200 */
    /* Probe scratch at FF B0+ must remain beyond the copied HRAM routine. */
    if (probe_cpu_access && routine_size > 0x30u) return NULL;

    uint16_t source_address = 0;
    emit_copy_to_hram(&main_program, &source_address, routine, routine_size);
    memcpy(rom + 0x150, main_program.bytes, main_program.size);
    memcpy(rom + source_address, routine, routine_size);

    /* After DMA, enable the LCD and halt while one complete frame is produced. */
    size_t post = 0x0200;
    if (probe_cpu_access) {
        rom[post++] = 0xF0; rom[post++] = 0xB0; /* blocked WRAM read result */
        rom[post++] = 0xEA; rom[post++] = 0x00; rom[post++] = 0xC2;
        rom[post++] = 0xFA; rom[post++] = 0x00; rom[post++] = 0xC0;
        rom[post++] = 0xEA; rom[post++] = 0x01; rom[post++] = 0xC2;
        rom[post++] = 0xF0; rom[post++] = 0xB1;
        rom[post++] = 0xEA; rom[post++] = 0x02; rom[post++] = 0xC2;
        rom[post++] = 0xF0; rom[post++] = 0xB2;
        rom[post++] = 0xEA; rom[post++] = 0x03; rom[post++] = 0xC2;
        rom[post++] = 0xFA; rom[post++] = 0x00; rom[post++] = 0x80;
        rom[post++] = 0xEA; rom[post++] = 0x05; rom[post++] = 0xC2;
        rom[post++] = 0xFA; rom[post++] = 0x00; rom[post++] = 0xFE;
        rom[post++] = 0xEA; rom[post++] = 0x06; rom[post++] = 0xC2;
    }
    rom[post++] = 0xF0; rom[post++] = 0x46; /* read FF46 after completion */
    rom[post++] = 0xEA; rom[post++] = 0x04; rom[post++] = 0xC2;
    rom[post++] = 0x3E; rom[post++] = 0x92; /* objects on, DMG BG off */
    rom[post++] = 0xE0; rom[post++] = 0x40;
    rom[post++] = 0x76;                      /* HALT */
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;

    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static int run_frame(gbb_instance *machine, uint8_t pixels[PIXELS]) {
    uint64_t remaining = UINT64_C(180000);
    while (remaining != 0) {
        gbb_run_result run = gbb_run(machine, remaining, NULL, 0);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE || run.reason == GBB_STOP_BUDGET);
        if (run.consumed_half_dots == 0) {
            REQUIRE(remaining < 32u); /* the next whole instruction is larger */
            break;
        }
        REQUIRE(run.consumed_half_dots <= remaining);
        remaining -= run.consumed_half_dots;
    }
    gbb_frame_info info = {0};
    gbb_error frame_error = gbb_copy_frame(machine, pixels, PIXELS, WIDTH, &info);
    if (frame_error != GBB_OK) {
        fprintf(stderr, "frame unavailable error=%d generation=%llu\n", frame_error,
                (unsigned long long)info.generation);
    }
    REQUIRE(frame_error == GBB_OK);
    REQUIRE(info.width == WIDTH && info.height == HEIGHT && info.generation != 0);
    return 0;
}

static int expect_dma_object(uint8_t source_page, int restart) {
    gbb_instance *machine = load_dma_guest(source_page, restart, 0, 0, 0);
    REQUIRE(machine != NULL);
    gbb_test_dma_event events[400];
    gbb_test_dma_observer_set(machine, events, sizeof(events) / sizeof(events[0]));
    uint8_t *pixels = malloc(PIXELS);
    REQUIRE(pixels != NULL);
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[3] == (restart ? 0u : 3u));
    REQUIRE(gbb_peek_ram(machine, 0xC204) == (restart ? 0xD0u : source_page));
    size_t event_count = gbb_test_dma_observer_count(machine);
    REQUIRE(event_count >= 162u);
    REQUIRE(events[0].access == 1u && events[0].address == 0xFF46u);
    REQUIRE(events[0].value == source_page);
    uint64_t start = events[0].time_half_dots;
    REQUIRE(events[1].access == 2u && events[1].address == 0xFE00u);
    REQUIRE(events[1].value == 16u && events[1].time_half_dots == start + 8u);
    if (!restart) REQUIRE(event_count == 162u);
    for (unsigned i = 0; i < 160u && !restart; ++i) {
        REQUIRE(events[i + 1u].access == 2u);
        REQUIRE(events[i + 1u].address == (uint16_t)(0xFE00u + i));
        REQUIRE(events[i + 1u].time_half_dots == start + ((uint64_t)i + 1u) * 8u);
        if (i >= 4u) REQUIRE(events[i + 1u].value == 0u);
    }
    if (!restart) {
        REQUIRE(events[161].access == 3u && events[161].address == 0xFF46u);
        REQUIRE(events[161].time_half_dots == start + 1280u);
    } else {
        size_t restart_start = 1u;
        while (restart_start < event_count &&
               !(events[restart_start].access == 1u && events[restart_start].address == 0xFF46u))
            ++restart_start;
        REQUIRE(restart_start < event_count);
        REQUIRE(events[restart_start].value == 0xD0u);
        REQUIRE(events[restart_start + 1u].access == 2u &&
                events[restart_start + 1u].address == 0xFE00u &&
                events[restart_start + 1u].value == 1u);
        for (unsigned i = 0; i < 160u; ++i) {
            REQUIRE(events[restart_start + 1u + i].access == 2u);
            REQUIRE(events[restart_start + 1u + i].address == (uint16_t)(0xFE00u + i));
        }
        REQUIRE(events[restart_start + 161u].access == 3u);
        REQUIRE(events[restart_start + 161u].address == 0xFF46u);
    }
    free(pixels);
    gbb_destroy(machine);
    return 0;
}

static int expect_no_dma_object(uint8_t source_page) {
    gbb_instance *machine = load_dma_guest(source_page, 0, 0, 0, 0);
    REQUIRE(machine != NULL);
    gbb_test_dma_event events[162];
    gbb_test_dma_observer_set(machine, events, 162);
    uint8_t pixels[PIXELS];
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[3] == 0u);
    REQUIRE(gbb_peek_ram(machine, 0xC204) == source_page);
    REQUIRE(gbb_test_dma_observer_count(machine) == 162u);
    REQUIRE(events[0].access == 1u && events[0].value == source_page);
    for (size_t i = 0; i < 160u; ++i)
        REQUIRE(events[i + 1u].value == 0xFFu);
    REQUIRE(events[161].access == 3u);
    gbb_destroy(machine);
    return 0;
}

static int dma_progress(void) {
    gbb_instance *machine = load_dma_guest(0xC0, 0, 0, 1, 0);
    REQUIRE(machine != NULL);
    gbb_test_dma_event dma_events[162];
    gbb_test_bus_event bus_events[512];
    gbb_test_dma_observer_set(machine, dma_events, 162);
    gbb_test_observer_set(machine, bus_events, 512);
    uint8_t pixels[PIXELS];
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[3] == 3u);
    REQUIRE(gbb_test_dma_observer_count(machine) == 162u);
    REQUIRE(gbb_peek_ram(machine, 0xC204) == 0xC0u);
    uint64_t start = dma_events[0].time_half_dots;
    REQUIRE(dma_events[1].time_half_dots == start + 8u);
    for (unsigned i = 0; i < 160u; ++i) {
        REQUIRE(dma_events[i + 1u].address == (uint16_t)(0xFE00u + i));
        REQUIRE(dma_events[i + 1u].time_half_dots == start + ((uint64_t)i + 1u) * 8u);
    }
    REQUIRE(dma_events[160].time_half_dots == start + 1280u);
    REQUIRE(dma_events[161].time_half_dots == start + 1280u);
    size_t found = 0;
    static const uint64_t deltas[] = {1272u, 1288u, 1304u};
    static const uint8_t values[] = {0xFFu, 8u, 0u};
    size_t event_count = gbb_test_observer_count(machine);
    for (size_t i = 0; i < event_count; ++i) {
        if (bus_events[i].access != 1u || bus_events[i].address < 0xC000u ||
            bus_events[i].address > 0xC002u) continue;
        REQUIRE(found < 3u);
        REQUIRE(bus_events[i].address == (uint16_t)(0xC000u + found));
        REQUIRE(bus_events[i].time_half_dots == start + deltas[found]);
        REQUIRE(bus_events[i].value == values[found]);
        ++found;
    }
    REQUIRE(found == 3u);
    gbb_destroy(machine);
    return 0;
}

static int dma_source_mapping(void) {
    static const uint8_t valid_pages[] = {0x80, 0x9F, 0xC0, 0xDF};
    for (size_t i = 0; i < sizeof(valid_pages); ++i)
        REQUIRE(expect_dma_object(valid_pages[i], 0) == 0);
    /* The official DMG manual excludes ROM pages; this ROM-only profile also
     * has no external cartridge RAM at A000-BFFF. */
    static const uint8_t unmapped_pages[] = {0x00, 0xA0, 0xBF, 0xE0, 0xFE};
    for (size_t i = 0; i < sizeof(unmapped_pages); ++i)
        REQUIRE(expect_no_dma_object(unmapped_pages[i]) == 0);
    return 0;
}

static int dma_start(void) {
    /* Corresponds to the first-round fresh-transfer M=0/M=1/M=2 access window
     * in pinned oam_dma_start.s. This original guest places INC B in OAM,
     * starts DMA by executing LD (HL),A from the OAM echo predecessor, and
     * observes the first startup instruction before the transfer can replace
     * it. It does not reproduce the upstream test's complete final register
     * tuple. The PPU remains disabled, so no scan/fetch arbitration is involved. */
    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    small_program p = {{0}, 0};
    emit(&p, 0xAF); emit(&p, 0xE0); emit(&p, 0x40); /* LCD off */
    emit_memory_byte(&p, 0x8000u, 0xD7u); /* DMA page begins with RST $10 */
    emit(&p, 0x21); emit16(&p, 0xFE00u); /* initialize OAM with INC B */
    emit(&p, 0x06); emit(&p, 0xA0u);
    emit(&p, 0x3E); emit(&p, 0x04u);
    size_t fill_loop = p.size;
    emit(&p, 0x22); emit(&p, 0x05); emit(&p, 0x20);
    size_t fill_relative = p.size;
    emit(&p, (uint8_t)((int)fill_loop - (int)(fill_relative + 1u)));
    emit_memory_byte(&p, 0xFDFFu, 0x77u); /* opcode LD (HL),A at FDFF */
    emit(&p, 0x21); emit16(&p, 0xFF46u);
    emit(&p, 0x3E); emit(&p, 0x80u);
    emit(&p, 0x06); emit(&p, 0x00u); /* B=0; first OAM instruction increments it */
    emit(&p, 0xC3); emit16(&p, 0xFDFFu);
    memcpy(rom + 0x150, p.bytes, p.size);
    rom[0x10] = 0x76; /* wait in RST $10 vector until the DMA source bus releases */
    rom[0x38] = 0x76; /* DMG blocked-bus open value can also dispatch RST $38 */
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_test_dma_event events[162];
    gbb_test_dma_observer_set(m, events, 162);
    gbb_run_result run = gbb_run(m, 12000u, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_test_dma_observer_count(m) == 162u);
    gbb_trace_record snapshot;
    extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);
    gbb_test_cpu_snapshot(m, &snapshot);
    REQUIRE(snapshot.b == 1u); /* upstream B=$01 startup observation */
    REQUIRE(events[0].access == 1u && events[0].value == 0x80u);
    REQUIRE(events[1].address == 0xFE00u && events[1].value == 0xD7u);
    REQUIRE(events[161].access == 3u && events[161].address == 0xFF46u);
    gbb_destroy(m);
    return 0;
}

static int dma_restart(void) {
    REQUIRE(expect_dma_object(0xC0u, 1) == 0);
    gbb_instance *m = load_dma_guest(0xC0u, 1, 0, 2, 0);
    REQUIRE(m != NULL);
    gbb_test_dma_event dma[400];
    gbb_test_bus_event bus[512];
    gbb_test_dma_observer_set(m, dma, 400);
    gbb_test_observer_set(m, bus, 512);
    uint8_t pixels[PIXELS];
    REQUIRE(run_frame(m, pixels) == 0);
    size_t dn = gbb_test_dma_observer_count(m), bn = gbb_test_observer_count(m);
    uint64_t restart_at = 0;
    for (size_t i = 0; i < dn; ++i)
        if (dma[i].access == 1u && dma[i].value == 0xD0u) restart_at = dma[i].time_half_dots;
    REQUIRE(restart_at != 0);
    static const uint64_t deltas[] = {1272u, 1288u, 1304u};
    static const uint8_t values[] = {0xFFu, 0x01u, 0x01u};
    size_t found = 0;
    for (size_t i = 0; i < bn; ++i)
        if (bus[i].address == 0xFE00u && bus[i].access == 1u) {
            REQUIRE(found < 3u);
            REQUIRE(bus[i].time_half_dots == restart_at + deltas[found]);
            REQUIRE(bus[i].value == values[found]);
            ++found;
        }
    REQUIRE(found == 3u);
    gbb_destroy(m);
    return 0;
}

static int run_budget(gbb_instance *machine, uint64_t budget);

/* The pinned Mooneye acceptance/oam_dma/reg_read.s checks that FF46 reads
 * retain the last written page before/after transfers and across restarts.
 * This is an original guest sequence: it copies that observable register
 * contract, not the upstream ROM or its PPU/DMA collision setup. */
static int dma_register_readback(void) {
    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    static const uint8_t routine[] = {
        0x3E, 0x9F, 0xE0, 0x46,       /* start page 9F, matching reg_read.s */
        0xF0, 0x46, 0xE0, 0xD0,       /* read immediate FF46 */
        0x3E, 0x42, 0xE0, 0x46,       /* restart value 42, matching reg_read.s */
        0xF0, 0x46, 0xE0, 0xD1,       /* read during replacement */
        0x76 /* keep execution in HRAM while the restarted transfer finishes */
    };
    small_program p = {{0}, 0};
    uint16_t source_address = 0;
    emit_copy_to_hram(&p, &source_address, routine, sizeof(routine));
    memcpy(rom + 0x150, p.bytes, p.size);
    memcpy(rom + source_address, routine, sizeof(routine));
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(run_budget(m, 5000u) == 0);
    REQUIRE(gbb_peek_ram(m, 0xFFD0u) == 0x9Fu);
    REQUIRE(gbb_peek_ram(m, 0xFFD1u) == 0x42u);
    gbb_destroy(m);
    m = load_dma_guest(0x8Fu, 0, 0, 0, 0);
    REQUIRE(m != NULL);
    uint8_t pixels[PIXELS];
    REQUIRE(run_frame(m, pixels) == 0);
    REQUIRE(gbb_peek_ram(m, 0xC204u) == 0x8Fu);
    gbb_destroy(m);
    m = load_dma_guest(0x3Fu, 0, 0, 0, 0);
    REQUIRE(m != NULL);
    REQUIRE(run_frame(m, pixels) == 0);
    REQUIRE(gbb_peek_ram(m, 0xC204u) == 0x3Fu);
    gbb_destroy(m);

    /* Original HRAM guest analogue of reg_read.s's two active writes: 90 is
     * decremented to 8F, then 40 to 3F; read each latest value and again after
     * the bounded transfer wait. The invalid source page is only a register
     * readback probe and does not change D-024's implemented source envelope. */
    uint8_t restart_rom[32768] = {0};
    restart_rom[0x100] = 0xC3; restart_rom[0x101] = 0x50; restart_rom[0x102] = 0x01;
    static const uint8_t restart_routine[] = {
        0x3E, 0x90, 0x3D, 0xE0, 0x46, 0xF0, 0x46, 0xE0, 0xD2,
        0x3E, 0x40, 0x3D, 0xE0, 0x46, 0xF0, 0x46, 0xE0, 0xD3,
        0x76
    };
    small_program restart_program = {{0}, 0};
    source_address = 0;
    emit_copy_to_hram(&restart_program, &source_address, restart_routine,
                      sizeof(restart_routine));
    memcpy(restart_rom + 0x150, restart_program.bytes, restart_program.size);
    memcpy(restart_rom + source_address, restart_routine, sizeof(restart_routine));
    restart_rom[0x134] = 0xE7;
    checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - restart_rom[i] - 1u);
    restart_rom[0x14D] = checksum;
    m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, restart_rom, sizeof(restart_rom)) == GBB_OK);
    REQUIRE(run_budget(m, 5000u) == 0);
    REQUIRE(gbb_peek_ram(m, 0xFFD2u) == 0x8Fu);
    REQUIRE(gbb_peek_ram(m, 0xFFD3u) == 0x3Fu);
    gbb_destroy(m);
    return 0;
}

static int dma_hram(void) {
    gbb_instance *machine = load_dma_guest(0xC0, 0, 1, 0, 0);
    REQUIRE(machine != NULL);
    gbb_test_dma_event events[162];
    gbb_test_dma_observer_set(machine, events, sizeof(events) / sizeof(events[0]));
    uint8_t pixels[PIXELS];
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[3] == 3u);
    REQUIRE(gbb_test_dma_observer_count(machine) == 162u);
    REQUIRE(gbb_peek_ram(machine, 0xC200) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC201) == 16u);
    REQUIRE(gbb_peek_ram(machine, 0xC202) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC203) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC205) == 16u);
    REQUIRE(gbb_peek_ram(machine, 0xC206) == 16u);
    gbb_destroy(machine);
    return 0;
}

static int dma_interrupt_stack(void) {
    gbb_instance *machine = load_dma_guest(0xC0, 0, 0, 0, 1);
    REQUIRE(machine != NULL);
    gbb_test_dma_event dma_events[162];
    gbb_test_bus_event bus_events[512];
    gbb_test_dma_observer_set(machine, dma_events, 162);
    gbb_test_observer_set(machine, bus_events, 512);
    for (size_t step = 0; step < 1000u && gbb_test_dma_observer_count(machine) == 0; ++step) {
        gbb_trace_record one;
        gbb_run_result run = gbb_run(machine, 128u, &one, 1u);
        REQUIRE(run.consumed_half_dots != 0);
        REQUIRE(run.reason == GBB_STOP_TRACE_FULL || run.reason == GBB_STOP_BUDGET);
    }
    REQUIRE(gbb_test_dma_observer_count(machine) == 6u); /* start plus five bytes */
    uint64_t start = dma_events[0].time_half_dots;
    gbb_trace_record snapshot;
    extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);
    gbb_test_cpu_snapshot(machine, &snapshot);
    REQUIRE(snapshot.pc == 0x0040u);

    unsigned stack_writes = 0;
    size_t event_count = gbb_test_observer_count(machine);
    for (size_t i = 0; i < event_count; ++i) {
        if (bus_events[i].time_half_dots < start || bus_events[i].access != 2u) continue;
        if (bus_events[i].address == 0xC001u) {
            REQUIRE(bus_events[i].time_half_dots == start + 16u);
            REQUIRE(bus_events[i].value == 0xFFu);
            ++stack_writes;
        } else if (bus_events[i].address == 0xC000u) {
            REQUIRE(bus_events[i].time_half_dots == start + 24u);
            REQUIRE(bus_events[i].value == 0x85u);
            ++stack_writes;
        }
    }
    REQUIRE(stack_writes == 2u);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 16u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 8u);

    gbb_trace_record fetch;
    gbb_run_result blocked_fetch = gbb_run(machine, 32u, &fetch, 1u);
    REQUIRE(blocked_fetch.consumed_half_dots == 32u && blocked_fetch.trace_count == 1u);
    REQUIRE(fetch.pc == 0x0040u && fetch.opcode[0] == 0xFFu);
    gbb_test_cpu_snapshot(machine, &snapshot);
    REQUIRE(snapshot.pc == 0x0038u);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 16u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 8u);
    gbb_destroy(machine);
    return 0;
}

static int run_budget(gbb_instance *machine, uint64_t budget) {
    while (budget != 0) {
        gbb_run_result run = gbb_run(machine, budget, NULL, 0);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE || run.reason == GBB_STOP_BUDGET);
        if (run.consumed_half_dots == 0) {
            REQUIRE(budget < 32u);
            return 0;
        }
        REQUIRE(run.consumed_half_dots <= budget);
        budget -= run.consumed_half_dots;
    }
    return 0;
}

static int dma_partition(void) {
    gbb_instance *whole = load_dma_guest(0xC0, 0, 0, 0, 0);
    gbb_instance *parts = load_dma_guest(0xC0, 0, 0, 0, 0);
    REQUIRE(whole != NULL && parts != NULL);
    gbb_test_dma_event whole_events[162], part_events[162];
    gbb_test_dma_observer_set(whole, whole_events, 162);
    gbb_test_dma_observer_set(parts, part_events, 162);
    uint8_t whole_pixels[PIXELS], part_pixels[PIXELS];
    REQUIRE(run_frame(whole, whole_pixels) == 0);
    REQUIRE(run_budget(parts, 40000u) == 0);
    REQUIRE(run_budget(parts, 60000u) == 0);
    REQUIRE(run_budget(parts, 80000u) == 0);
    gbb_frame_info info = {0};
    REQUIRE(gbb_copy_frame(parts, part_pixels, PIXELS, WIDTH, &info) == GBB_OK);
    REQUIRE(info.generation != 0);
    REQUIRE(gbb_test_dma_observer_count(whole) == 162u);
    REQUIRE(gbb_test_dma_observer_count(parts) == 162u);
    REQUIRE(memcmp(whole_pixels, part_pixels, PIXELS) == 0);
    for (size_t i = 0; i < 162u; ++i) {
        REQUIRE(whole_events[i].time_half_dots == part_events[i].time_half_dots);
        REQUIRE(whole_events[i].address == part_events[i].address);
        REQUIRE(whole_events[i].access == part_events[i].access);
        REQUIRE(whole_events[i].value == part_events[i].value);
    }
    gbb_destroy(whole);
    gbb_destroy(parts);
    return 0;
}

static int dma_contention(void) {
    gbb_instance *active = load_dma_guest(0xC0, 0, 0, 0, 0);
    gbb_instance *idle = load_dma_guest(0xC0, 0, 0, 0, 0);
    REQUIRE(active != NULL && idle != NULL);
    gbb_test_dma_event active_events[162], idle_events[162];
    gbb_test_dma_observer_set(active, active_events, 162);
    gbb_test_dma_observer_set(idle, idle_events, 162);

    for (size_t step = 0; step < 1000u && gbb_test_dma_observer_count(active) == 0; ++step) {
        gbb_trace_record one;
        gbb_run_result run = gbb_run(active, 128u, &one, 1u);
        REQUIRE(run.consumed_half_dots != 0);
        REQUIRE(run.reason == GBB_STOP_TRACE_FULL || run.reason == GBB_STOP_BUDGET);
    }
    REQUIRE(gbb_test_dma_observer_count(active) == 1u);
    uint64_t start = active_events[0].time_half_dots;
    REQUIRE(active_events[0].address == 0xFF46u && active_events[0].access == 1u);

    gbb_run_result in_flight = gbb_run(active, 64u, NULL, 0);
    REQUIRE(in_flight.consumed_half_dots != 0u && in_flight.consumed_half_dots <= 64u);
    size_t in_flight_count = gbb_test_dma_observer_count(active);
    REQUIRE(in_flight_count > 1u && in_flight_count < 162u);
    for (size_t i = 1; i < in_flight_count; ++i) {
        REQUIRE(active_events[i].address == (uint16_t)(0xFE00u + i - 1u));
        REQUIRE(active_events[i].access == 2u);
        REQUIRE(active_events[i].time_half_dots == start + (uint64_t)i * 8u);
    }

    gbb_run_result independent = gbb_run(idle, 128u, NULL, 0);
    REQUIRE(independent.consumed_half_dots != 0u && independent.consumed_half_dots <= 128u);
    REQUIRE(gbb_test_dma_observer_count(idle) == 0u);

    REQUIRE(gbb_reset(active) == GBB_OK);
    size_t reset_count = gbb_test_dma_observer_count(active);
    REQUIRE(reset_count == in_flight_count);
    gbb_run_result after_reset = gbb_run(active, 128u, NULL, 0);
    REQUIRE(after_reset.consumed_half_dots != 0u && after_reset.consumed_half_dots <= 128u);
    REQUIRE(gbb_test_dma_observer_count(active) == reset_count);
    REQUIRE(gbb_test_dma_observer_count(idle) == 0u);

    gbb_destroy(active);
    gbb_destroy(idle);
    return 0;
}

static gbb_instance *load_ppu_dma_overlap_guest(unsigned delay_nops, int dma_enabled,
                                                 unsigned cpu_nops, int dma_before_lcd,
                                                 uint8_t object_x, uint8_t fine_scroll) {
    small_program p = {{0}, 0};
    emit(&p, 0xAF); emit(&p, 0xE0); emit(&p, 0x40); /* LCD off */
    emit(&p, 0x3E); emit(&p, 0xE4); emit(&p, 0xE0); emit(&p, 0x48); /* OBP0 */
    emit(&p, 0xAF); emit(&p, 0xE0); emit(&p, 0x47); /* BGP maps background to 0 */
    for (unsigned row = 0; row < 8; ++row) {
        emit_memory_byte(&p, (uint16_t)(0x8000u + row * 2u), 0xFFu); /* OBJ 1 */
        emit_memory_byte(&p, (uint16_t)(0x8001u + row * 2u), 0x00u);
        emit_memory_byte(&p, (uint16_t)(0x8010u + row * 2u), 0x00u); /* OBJ 2 */
        emit_memory_byte(&p, (uint16_t)(0x8011u + row * 2u), 0xFFu);
    }
    emit_source_record(&p, 0xFE00u, 16u);
    emit_memory_byte(&p, 0xFE01u, object_x);
    emit_memory_byte(&p, 0xFE02u, 0u);
    emit_memory_byte(&p, 0xFE03u, 0u);
    emit_source_record(&p, 0xFE04u, 17u);
    emit_memory_byte(&p, 0xFE05u, 8u);
    emit_memory_byte(&p, 0xFE06u, 0u);
    emit_memory_byte(&p, 0xFE07u, 0u);
    emit_memory_byte(&p, 0xFE10u, 0u);  /* old aligned DMA word, object is offscreen */
    emit_memory_byte(&p, 0xFE11u, 0x10u); /* old attributes select OBP1 */
    emit_source_record(&p, 0xFE78u, 16u); /* object 30, sampled after DMA starts */
    emit_memory_byte(&p, 0xFE79u, 24u);
    for (unsigned i = 0; i < 160u; ++i) {
        /* DMA destination words are tile 1 / attributes 0. */
        uint8_t byte = i == 0u ? 16u : i == 1u ? object_x : i == 2u ? 1u :
                       i == 3u ? 0u : i == 4u ? 17u : i == 5u ? 8u :
                       i == 6u ? 1u : i == 7u ? 0u : i == 120u ? 16u :
                       i == 121u ? 24u : i == 122u ? 1u : i == 123u ? 0u :
                       ((i & 1u) == 0 ? 1u : 0u);
        emit_memory_byte(&p, (uint16_t)(0xC000u + i), byte);
    }
    uint8_t routine[48];
    size_t rn = 0;
    if (cpu_nops != UINT32_MAX) {
        routine[rn++] = 0x21; routine[rn++] = 0x00; routine[rn++] = 0xFE;
    }
    if (dma_before_lcd) {
        routine[rn++] = 0x3E; routine[rn++] = 0xC0;
        routine[rn++] = 0xE0; routine[rn++] = 0x46;
        routine[rn++] = 0x06; routine[rn++] = 40u;
        size_t loop = rn;
        routine[rn++] = 0x05;
        routine[rn++] = 0x20;
        routine[rn++] = (uint8_t)((int)loop - (int)(rn + 1u));
        routine[rn++] = 0x3E; routine[rn++] = 0x93;
        routine[rn++] = 0xE0; routine[rn++] = 0x40;
    } else {
        if (fine_scroll != 0u) {
            routine[rn++] = 0x3E; routine[rn++] = fine_scroll;
            routine[rn++] = 0xE0; routine[rn++] = 0x43;
        }
        routine[rn++] = 0x3E; routine[rn++] = 0x93; /* LCD + BG + OBJ */
        routine[rn++] = 0xE0; routine[rn++] = 0x40;
        for (unsigned i = 0; i < delay_nops; ++i) routine[rn++] = 0x00;
        if (dma_enabled) {
            routine[rn++] = 0x3E; routine[rn++] = 0xC0;
            routine[rn++] = 0xE0; routine[rn++] = 0x46;
        }
    }
    if (cpu_nops != UINT32_MAX) {
        for (unsigned i = 0; i < cpu_nops; ++i) routine[rn++] = 0x00;
        routine[rn++] = 0x7E; /* blocked OAM read, timestamped by test observer */
    }
    routine[rn++] = 0x76; /* HALT in HRAM during DMA */
    uint16_t routine_address = 0;
    emit_copy_to_hram(&p, &routine_address, routine, rn);

    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    memcpy(rom + 0x150, p.bytes, p.size);
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    (void)routine_address;
    return machine;
}

static int dma_ppu_overlap(void) {
    uint8_t pixels[PIXELS];
    gbb_instance *baseline = load_ppu_dma_overlap_guest(0u, 0, UINT32_MAX, 0, 8u, 0u);
    REQUIRE(baseline != NULL);
    REQUIRE(run_frame(baseline, pixels) == 0);
    REQUIRE(pixels[0] == 1u && pixels[16] == 1u && pixels[WIDTH] == 1u);
    gbb_destroy(baseline);

    gbb_instance *machine = load_ppu_dma_overlap_guest(0u, 1, UINT32_MAX, 0, 8u, 0u);
    REQUIRE(machine != NULL);
    gbb_test_dma_event dma[162];
    gbb_test_bus_event fetches[1200];
    gbb_test_dma_observer_set(machine, dma, 162);
    gbb_test_ppu_observer_set(machine, fetches, 1200);
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[0] == 3u); /* first byte updated; paired attribute is still pre-DMA */
    REQUIRE(pixels[16] == 0u); /* later mode-2 entry sampled during DMA */
    REQUIRE(pixels[WIDTH] == 0u); /* line-1 object was scanned during DMA */
    REQUIRE(gbb_test_dma_observer_count(machine) == 162u);
    REQUIRE(dma[0].access == 1u && dma[0].value == 0xC0u);
    REQUIRE(dma[1].address == 0xFE00u && dma[1].value == 16u);
    REQUIRE(dma[1].time_half_dots == dma[0].time_half_dots + 8u);
    REQUIRE(dma[160].address == 0xFE9Fu && dma[161].access == 3u);
    gbb_destroy(machine);
    gbb_instance *partial = load_ppu_dma_overlap_guest(10u, 1, UINT32_MAX, 0, 8u, 0u);
    REQUIRE(partial != NULL);
    gbb_test_bus_event scan_events[1200];
    gbb_test_ppu_observer_set(partial, scan_events, 1200);
    REQUIRE(run_frame(partial, pixels) == 0);
    REQUIRE(pixels[16] == 2u && pixels[WIDTH] == 0u);
    uint64_t scan_boundary = 0;
    size_t scan_count = gbb_test_ppu_observer_count(partial);
    for (size_t i = 0; i < scan_count; ++i)
        if (scan_events[i].access == 9u && scan_events[i].address == 0xFE1Eu) {
            scan_boundary = scan_events[i].time_half_dots;
            REQUIRE(scan_events[i].value == 1u);
            break;
        }
    REQUIRE(scan_boundary != 0u);
    gbb_destroy(partial);

    gbb_instance *scan_parts = load_ppu_dma_overlap_guest(10u, 1, UINT32_MAX, 0, 8u, 0u);
    REQUIRE(scan_parts != NULL);
    gbb_test_bus_event split_scan_events[1200];
    gbb_test_ppu_observer_set(scan_parts, split_scan_events, 1200);
    REQUIRE(run_budget(scan_parts, scan_boundary - 32u) == 0);
    REQUIRE(run_budget(scan_parts, 32u) == 0);
    REQUIRE(run_budget(scan_parts, 180000u - scan_boundary) == 0);
    uint8_t split_scan_pixels[PIXELS];
    gbb_frame_info split_scan_info = {0};
    REQUIRE(gbb_copy_frame(scan_parts, split_scan_pixels, PIXELS, WIDTH,
                           &split_scan_info) == GBB_OK);
    REQUIRE(memcmp(pixels, split_scan_pixels, PIXELS) == 0);
    REQUIRE(gbb_test_ppu_observer_count(scan_parts) == scan_count);
    for (size_t i = 0; i < scan_count; ++i) {
        REQUIRE(split_scan_events[i].time_half_dots == scan_events[i].time_half_dots);
        REQUIRE(split_scan_events[i].address == scan_events[i].address);
        REQUIRE(split_scan_events[i].access == scan_events[i].access);
        REQUIRE(split_scan_events[i].value == scan_events[i].value);
    }
    gbb_destroy(scan_parts);

    gbb_instance *ended_before_scan = load_ppu_dma_overlap_guest(0u, 1, UINT32_MAX, 1, 8u, 0u);
    REQUIRE(ended_before_scan != NULL);
    REQUIRE(run_frame(ended_before_scan, pixels) == 0);
    REQUIRE(pixels[0] == 2u && pixels[16] == 2u && pixels[WIDTH] == 2u);
    gbb_destroy(ended_before_scan);

    return 0;
}

static int dma_ppu_word_boundaries(void) {
    static const uint8_t object_x[] = {8u, 14u};
    static const int expected_delta[] = {-2, 2};
    static const unsigned pixel_x[] = {0u, 6u};
    static const unsigned dma_event_index[] = {18u, 19u};
    static const uint8_t expected_shade[] = {3u, 2u};
    uint8_t pixels[PIXELS];
    for (size_t scenario = 0; scenario < 2u; ++scenario) {
        gbb_instance *machine = load_ppu_dma_overlap_guest(0u, 1, 16u, 0,
                                                            object_x[scenario], 3u);
        REQUIRE(machine != NULL);
        gbb_test_dma_event dma[162];
        gbb_test_bus_event ppu[1200];
        gbb_test_dma_observer_set(machine, dma, 162);
        gbb_test_ppu_observer_set(machine, ppu, 1200);
        REQUIRE(run_frame(machine, pixels) == 0);
        REQUIRE(gbb_test_dma_observer_count(machine) == 162u);
        uint64_t fetch_time = 0;
        uint8_t fetched_tile = 0xFFu;
        size_t count = gbb_test_ppu_observer_count(machine);
        for (size_t i = 0; i < count; ++i)
            if (ppu[i].access == 8u && ppu[i].address == 0xFE00u) {
                fetch_time = ppu[i].time_half_dots;
                fetched_tile = ppu[i].value;
                break;
            }
        REQUIRE(fetch_time != 0u && fetched_tile == 1u);
        REQUIRE(dma[dma_event_index[scenario]].access == 2u);
        REQUIRE((int64_t)fetch_time -
                (int64_t)dma[dma_event_index[scenario]].time_half_dots ==
                expected_delta[scenario]);
        REQUIRE(pixels[pixel_x[scenario]] == expected_shade[scenario]);
        gbb_destroy(machine);
    }
    return 0;
}

static int dma_ppu_cpu_collision(void) {
    uint8_t pixels[PIXELS];
    gbb_instance *machine = load_ppu_dma_overlap_guest(0u, 1, 16u, 0, 8u, 0u);
    gbb_instance *parts = load_ppu_dma_overlap_guest(0u, 1, 16u, 0, 8u, 0u);
    REQUIRE(machine != NULL && parts != NULL);
    gbb_test_dma_event dma[162];
    gbb_test_bus_event bus[6000], ppu[1200];
    gbb_test_dma_event part_dma[162];
    gbb_test_bus_event part_bus[6000], part_ppu[1200];
    gbb_test_dma_observer_set(machine, dma, 162);
    gbb_test_observer_set(machine, bus, 6000);
    gbb_test_ppu_observer_set(machine, ppu, 1200);
    gbb_test_dma_observer_set(parts, part_dma, 162);
    gbb_test_observer_set(parts, part_bus, 6000);
    gbb_test_ppu_observer_set(parts, part_ppu, 1200);
    REQUIRE(run_frame(machine, pixels) == 0);
    size_t dn = gbb_test_dma_observer_count(machine);
    size_t bn = gbb_test_observer_count(machine);
    size_t pn = gbb_test_ppu_observer_count(machine);
    REQUIRE(dn == 162u);
    uint64_t collision = 0;
    unsigned dma_matches = 0, ppu_matches = 0, cpu_matches = 0;
    for (size_t i = 1; i < dn; ++i) {
        if (dma[i].address != 0xFE10u || dma[i].access != 2u || dma[i].value != 1u) continue;
        for (size_t j = 0; j < pn; ++j)
            if (ppu[j].address == 0xFE00u && ppu[j].access == 8u &&
                ppu[j].time_half_dots == dma[i].time_half_dots && ppu[j].value == 1u) {
                collision = ppu[j].time_half_dots;
                ++dma_matches;
                ++ppu_matches;
            }
        for (size_t j = 0; j < bn; ++j)
            if (bus[j].address == 0xFE00u && bus[j].access == 1u &&
                bus[j].time_half_dots == dma[i].time_half_dots && bus[j].value == 0xFFu) {
                collision = bus[j].time_half_dots;
                ++cpu_matches;
            }
    }
    REQUIRE(collision != 0u && dma_matches == 1u && ppu_matches == 1u && cpu_matches == 1u);
    REQUIRE(dma[16].address == 0xFE0Fu && dma[17].address == 0xFE10u);
    REQUIRE(dma[17].time_half_dots == collision && dma[17].value == 1u);
    REQUIRE(pixels[0] == 3u); /* DMA-first tie sees tile 1 and the still-old OBP1 attribute */
    REQUIRE(pixels[16] == 0u); /* overlapping object remains suppressed */
    REQUIRE(run_budget(parts, collision - 32u) == 0);
    REQUIRE(run_budget(parts, 32u) == 0); /* second call straddles the observed collision */
    REQUIRE(run_budget(parts, 180000u - collision) == 0);
    uint8_t part_pixels[PIXELS];
    gbb_frame_info part_info = {0};
    REQUIRE(gbb_copy_frame(parts, part_pixels, PIXELS, WIDTH, &part_info) == GBB_OK);
    REQUIRE(part_pixels[0] == 3u && part_pixels[16] == 0u);
    REQUIRE(gbb_test_dma_observer_count(parts) == dn);
    REQUIRE(gbb_test_observer_count(parts) == bn);
    REQUIRE(gbb_test_ppu_observer_count(parts) == pn);
    for (size_t i = 0; i < dn; ++i) {
        REQUIRE(dma[i].time_half_dots == part_dma[i].time_half_dots);
        REQUIRE(dma[i].address == part_dma[i].address);
        REQUIRE(dma[i].access == part_dma[i].access);
        REQUIRE(dma[i].value == part_dma[i].value);
    }
    for (size_t i = 0; i < bn; ++i)
        REQUIRE(memcmp(&bus[i], &part_bus[i], sizeof(bus[i])) == 0);
    for (size_t i = 0; i < pn; ++i)
        REQUIRE(memcmp(&ppu[i], &part_ppu[i], sizeof(ppu[i])) == 0);
    REQUIRE(memcmp(pixels, part_pixels, PIXELS) == 0);
    gbb_destroy(parts);
    gbb_destroy(machine);
    return 0;
}

static gbb_instance *load_active_mode_guest(uint8_t target_mode) {
    small_program p = {{0}, 0};
    emit(&p, 0xAF); emit(&p, 0xE0); emit(&p, 0x40); /* LCD off */
    emit_memory_byte(&p, 0x8000u, 0x11u);
    emit_memory_byte(&p, 0xFE00u, 0x22u);
    emit_memory_byte(&p, 0xC000u, 0x44u);
    uint8_t routine[64];
    size_t n = 0;
    routine[n++] = 0x21; routine[n++] = 0x00; routine[n++] = 0xFE;
    routine[n++] = 0x06; routine[n++] = 0x77;   /* value for both bus writes */
    routine[n++] = 0x3E; routine[n++] = 0x91; /* LCD + BG */
    routine[n++] = 0xE0; routine[n++] = 0x40;
    if (target_mode != 2u) {
        size_t loop = n;
        routine[n++] = 0xF0; routine[n++] = 0x41; /* STAT */
        routine[n++] = 0xE6; routine[n++] = 0x03;
        routine[n++] = 0xFE; routine[n++] = target_mode;
        routine[n++] = 0x20;
        routine[n] = (uint8_t)((int)loop - (int)(n + 1u));
        ++n;
    }
    routine[n++] = 0x3E; routine[n++] = 0xC0;
    routine[n++] = 0xE0; routine[n++] = 0x46; /* DMA in selected PPU mode */
    routine[n++] = 0x7E;                         /* OAM read */
    routine[n++] = 0x78;                         /* LD A,B */
    routine[n++] = 0x77;                         /* OAM write */
    routine[n++] = 0x26; routine[n++] = 0x80;   /* HL=8000 */
    routine[n++] = 0x7E;                         /* VRAM read */
    routine[n++] = 0x78;
    routine[n++] = 0x77;                         /* VRAM write */
    routine[n++] = 0x06; routine[n++] = 0xFF;
    size_t wait = n;
    routine[n++] = 0x05; routine[n++] = 0x20;
    routine[n] = (uint8_t)((int)wait - (int)(n + 1u));
    ++n;
    routine[n++] = 0xAF; routine[n++] = 0xE0; routine[n++] = 0x40; /* LCD off */
    routine[n++] = 0xFA; routine[n++] = 0x00; routine[n++] = 0x80;
    routine[n++] = 0xEA; routine[n++] = 0x00; routine[n++] = 0xC1;
    routine[n++] = 0xFA; routine[n++] = 0x00; routine[n++] = 0xFE;
    routine[n++] = 0xEA; routine[n++] = 0x01; routine[n++] = 0xC1;
    routine[n++] = 0x76;
    uint16_t routine_address = 0;
    emit_copy_to_hram(&p, &routine_address, routine, n);
    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    memcpy(rom + 0x150, p.bytes, p.size);
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    (void)routine_address;
    return machine;
}

static uint8_t ppu_mode_at(const gbb_test_bus_event *events, size_t count,
                           uint64_t time) {
    uint8_t mode = 0xFFu;
    for (size_t i = 0; i < count; ++i)
        if (events[i].access == 4u && events[i].time_half_dots <= time)
            mode = events[i].value;
    return mode;
}

static int dma_active_mode_matrix(void) {
    for (uint8_t target = 0; target < 4u; ++target) {
        gbb_instance *machine = load_active_mode_guest(target);
        REQUIRE(machine != NULL);
        gbb_test_dma_event dma[162];
        gbb_test_bus_event bus[6000], ppu[1200];
        gbb_test_dma_observer_set(machine, dma, 162);
        gbb_test_observer_set(machine, bus, 6000);
        gbb_test_ppu_observer_set(machine, ppu, 1200);
        gbb_run_result run = gbb_run(machine, 150000u, NULL, 0);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE || run.reason == GBB_STOP_BUDGET);
        size_t dn = gbb_test_dma_observer_count(machine);
        size_t bn = gbb_test_observer_count(machine);
        size_t pn = gbb_test_ppu_observer_count(machine);
        REQUIRE(dn == 162u);
        uint64_t start = dma[0].time_half_dots;
        REQUIRE(ppu_mode_at(ppu, pn, start) == target);
        unsigned vram_reads = 0, vram_writes = 0, oam_reads = 0, oam_writes = 0;
        for (size_t i = 0; i < bn; ++i) {
            if (bus[i].time_half_dots < start ||
                bus[i].time_half_dots > start + 1280u ||
                (bus[i].address != 0x8000u && bus[i].address != 0xFE00u)) continue;
            if (bus[i].address == 0x8000u && bus[i].access == 1u) {
                REQUIRE(bus[i].value == 0xFFu);
                REQUIRE(ppu_mode_at(ppu, pn, bus[i].time_half_dots) == target);
                ++vram_reads;
            } else if (bus[i].address == 0x8000u && bus[i].access == 2u) {
                REQUIRE(bus[i].value == 0x77u);
                REQUIRE(ppu_mode_at(ppu, pn, bus[i].time_half_dots) == target);
                ++vram_writes;
            } else if (bus[i].address == 0xFE00u && bus[i].access == 1u) {
                REQUIRE(bus[i].value == 0xFFu);
                REQUIRE(ppu_mode_at(ppu, pn, bus[i].time_half_dots) == target);
                ++oam_reads;
            } else if (bus[i].address == 0xFE00u && bus[i].access == 2u) {
                REQUIRE(bus[i].value == 0x77u);
                REQUIRE(ppu_mode_at(ppu, pn, bus[i].time_half_dots) == target);
                ++oam_writes;
            }
        }
        REQUIRE(vram_reads == 1u && vram_writes == 1u);
        REQUIRE(oam_reads == 1u && oam_writes == 1u);
        REQUIRE(gbb_peek_ram(machine, 0xC100u) == 0x11u);
        REQUIRE(gbb_peek_ram(machine, 0xC101u) == 0x44u);
        gbb_destroy(machine);
    }
    return 0;
}

static void rom_emit8(uint8_t rom[32768], size_t *pc, uint8_t value) {
    if (*pc < 32768u) rom[(*pc)++] = value;
}

static void rom_emit16(uint8_t rom[32768], size_t *pc, uint16_t value) {
    rom_emit8(rom, pc, (uint8_t)value);
    rom_emit8(rom, pc, (uint8_t)(value >> 8));
}

static gbb_instance *load_lock_guest(uint16_t address) {
    uint8_t rom[32768] = {0};
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    size_t pc = 0x150;
    rom_emit8(rom, &pc, 0xAF); /* LCD off */
    rom_emit8(rom, &pc, 0xE0); rom_emit8(rom, &pc, 0x40);
    rom_emit8(rom, &pc, 0x21); rom_emit16(rom, &pc, address);
    rom_emit8(rom, &pc, 0x3E); rom_emit8(rom, &pc, 0x55);
    rom_emit8(rom, &pc, 0x77); /* initialize while LCD is off */
    rom_emit8(rom, &pc, 0x7E); /* LCD-off read returns the initialized byte */
    rom_emit8(rom, &pc, 0x3E); rom_emit8(rom, &pc, 0x91);
    rom_emit8(rom, &pc, 0xE0); rom_emit8(rom, &pc, 0x40); /* enable; anchor T */
    rom_emit8(rom, &pc, 0x7E); /* mode 2 read at T+16 */
    rom_emit8(rom, &pc, 0x3E); rom_emit8(rom, &pc, 0x33);
    rom_emit8(rom, &pc, 0x77); /* mode 2 write at T+40 */
    for (unsigned i = 0; i < 11u; ++i) rom_emit8(rom, &pc, 0x00);
    rom_emit8(rom, &pc, 0x7E); /* immediately before mode 2 -> 3 */
    rom_emit8(rom, &pc, 0x7E); /* immediately after mode 2 -> 3 */
    rom_emit8(rom, &pc, 0x7E); /* mode 3 read at T+168 */
    rom_emit8(rom, &pc, 0x3E); rom_emit8(rom, &pc, 0xAA);
    rom_emit8(rom, &pc, 0x77); /* mode 3 write at T+192 */
    for (unsigned i = 0; i < 33u; ++i) rom_emit8(rom, &pc, 0x00);
    rom_emit8(rom, &pc, 0x7E); /* mode 3 read at T+496 */
    rom_emit8(rom, &pc, 0x7E); /* first following HBlank read at T+512 */
    rom_emit8(rom, &pc, 0x3E); rom_emit8(rom, &pc, 0x66);
    rom_emit8(rom, &pc, 0x77); /* mode 0 write bus phase at T+544 */
    for (unsigned i = 0; i < 16346u; ++i) rom_emit8(rom, &pc, 0x00);
    rom_emit8(rom, &pc, 0x7E); /* VBlank/mode 1 read at T+131328 */
    rom_emit8(rom, &pc, 0x76);
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static int check_ppu_lock(uint16_t address, int vram) {
    gbb_instance *machine = load_lock_guest(address);
    REQUIRE(machine != NULL);
    gbb_test_bus_event events[32];
    gbb_test_observer_set(machine, events, 32);
    gbb_run_result run = gbb_run(machine, 140000u, NULL, 0);
    if (run.reason != GBB_STOP_HALTED_IDLE && run.reason != GBB_STOP_BUDGET)
        fprintf(stderr, "lock guest stopped reason=%d consumed=%llu\n", run.reason,
                (unsigned long long)run.consumed_half_dots);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE || run.reason == GBB_STOP_BUDGET);
    size_t count = gbb_test_observer_count(machine);
    uint64_t enable = UINT64_MAX;
    for (size_t i = 0; i < count; ++i)
        if (events[i].address == 0xFF40u && events[i].access == 2u &&
            events[i].value == 0x91u) enable = events[i].time_half_dots;
    REQUIRE(enable != UINT64_MAX);
    static const uint64_t read_deltas[] = {16u, 152u, 168u, 184u, 496u, 512u, 131328u};
    uint8_t expected[7];
    if (vram) {
        const uint8_t values[] = {0x55u, 0x33u, 0xFFu, 0xFFu, 0xFFu, 0x33u, 0x66u};
        memcpy(expected, values, sizeof(expected));
    } else {
        const uint8_t values[] = {0xFFu, 0xFFu, 0xFFu, 0xFFu, 0xFFu, 0x55u, 0x66u};
        memcpy(expected, values, sizeof(expected));
    }
    size_t reads = 0, lcd_off_reads = 0;
    for (size_t i = 0; i < count; ++i) {
        if (events[i].address != address || events[i].access != 1u) continue;
        if (events[i].time_half_dots < enable) {
            REQUIRE(events[i].value == 0x55u);
            ++lcd_off_reads;
            continue;
        }
        REQUIRE(reads < 7u);
        REQUIRE(events[i].time_half_dots == enable + read_deltas[reads]);
        REQUIRE(events[i].value == expected[reads]);
        ++reads;
    }
    REQUIRE(lcd_off_reads == 1u);
    REQUIRE(reads == 7u);
    gbb_destroy(machine);
    return 0;
}

static int dma_vram_lock(void) { return check_ppu_lock(0x8000u, 1); }
static int dma_oam_lock(void) { return check_ppu_lock(0xFE00u, 0); }

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case = argv[1];
    if (strcmp(argv[1], "dma_progress") == 0) return dma_progress();
    if (strcmp(argv[1], "dma_start") == 0) return dma_start();
    if (strcmp(argv[1], "dma_restart") == 0) return dma_restart();
    if (strcmp(argv[1], "dma_register_readback") == 0) {
        int result = dma_register_readback();
        if (result == 0) printf("TAP version 13\n1..1\nok 1 - dma_register_readback\n");
        return result;
    }
    if (strcmp(argv[1], "dma_source_mapping") == 0) return dma_source_mapping();
    if (strcmp(argv[1], "dma_hram") == 0) return dma_hram();
    if (strcmp(argv[1], "dma_interrupt_stack") == 0) return dma_interrupt_stack();
    if (strcmp(argv[1], "dma_partition") == 0) return dma_partition();
    if (strcmp(argv[1], "dma_contention") == 0) return dma_contention();
    if (strcmp(argv[1], "dma_ppu_overlap") == 0) return dma_ppu_overlap();
    if (strcmp(argv[1], "dma_ppu_cpu_collision") == 0) return dma_ppu_cpu_collision();
    if (strcmp(argv[1], "dma_ppu_word_boundaries") == 0) return dma_ppu_word_boundaries();
    if (strcmp(argv[1], "dma_active_mode_matrix") == 0) return dma_active_mode_matrix();
    if (strcmp(argv[1], "dma_vram_lock") == 0) return dma_vram_lock();
    if (strcmp(argv[1], "dma_oam_lock") == 0) return dma_oam_lock();
    return 2;
}
