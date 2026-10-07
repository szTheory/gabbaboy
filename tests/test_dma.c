#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WIDTH 160u
#define HEIGHT 144u
#define PIXELS (WIDTH * HEIGHT)
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

typedef struct {
    uint8_t bytes[128];
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
        emit_source_record(&main_program, 0xD000, 0u); /* replacement would hide OBJ 0 */
    if (interrupt_probe) {
        emit(&main_program, 0x31); emit16(&main_program, 0xC002); /* SP=C002 */
        emit(&main_program, 0x3E); emit(&main_program, 1u);
        emit(&main_program, 0xE0); emit(&main_program, 0x0F); /* pending VBlank */
        emit(&main_program, 0xEA); emit16(&main_program, 0xFFFF); /* enable VBlank */
    }

    uint8_t routine[32];
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
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0xA0;
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0x77;
        routine[routine_size++] = 0x02;  /* blocked CPU write to C000 */
    }
    if (boundary_probe) {
        routine[routine_size++] = 0x21; routine[routine_size++] = 0x00;
        routine[routine_size++] = 0xC0; /* LD HL,C000 */
        routine[routine_size++] = 0x06; routine[routine_size++] = 0x25;
        routine[routine_size++] = 0x05; /* 37-cycle loop and six NOPs */
        routine[routine_size++] = 0x20; routine[routine_size++] = 0xFD;
        for (unsigned i = 0; i < 6; ++i) routine[routine_size++] = 0x00;
        routine[routine_size++] = 0x2A; /* reads immediately before and after end */
        routine[routine_size++] = 0x2A;
        routine[routine_size++] = 0x2A;
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

    uint16_t source_address = 0;
    emit_copy_to_hram(&main_program, &source_address, routine, routine_size);
    memcpy(rom + 0x150, main_program.bytes, main_program.size);
    memcpy(rom + source_address, routine, routine_size);

    /* After DMA, enable the LCD and halt while one complete frame is produced. */
    size_t post = 0x0200;
    if (probe_cpu_access) {
        rom[post++] = 0xF0; rom[post++] = 0xA0; /* LDH A,[A0] */
        rom[post++] = 0xEA; rom[post++] = 0x00; rom[post++] = 0xC2;
        rom[post++] = 0xFA; rom[post++] = 0x00; rom[post++] = 0xC0;
        rom[post++] = 0xEA; rom[post++] = 0x01; rom[post++] = 0xC2;
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
    gbb_test_dma_event events[162];
    gbb_test_dma_observer_set(machine, events, sizeof(events) / sizeof(events[0]));
    uint8_t *pixels = malloc(PIXELS);
    REQUIRE(pixels != NULL);
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[3] == 3u); /* source byte 0x10 creates OBJ color 1 at x=3 */
    REQUIRE(gbb_peek_ram(machine, 0xC204) == source_page);
    REQUIRE(gbb_test_dma_observer_count(machine) == 162u);
    REQUIRE(events[0].access == 1u && events[0].address == 0xFF46u);
    REQUIRE(events[0].value == source_page);
    uint64_t start = events[0].time_half_dots;
    REQUIRE(events[1].access == 2u && events[1].address == 0xFE00u);
    REQUIRE(events[1].value == 16u && events[1].time_half_dots == start + 8u);
    for (unsigned i = 0; i < 160u; ++i) {
        REQUIRE(events[i + 1u].access == 2u);
        REQUIRE(events[i + 1u].address == (uint16_t)(0xFE00u + i));
        REQUIRE(events[i + 1u].time_half_dots == start + ((uint64_t)i + 1u) * 8u);
        if (i >= 4u) REQUIRE(events[i + 1u].value == 0u);
    }
    REQUIRE(events[161].access == 3u && events[161].address == 0xFF46u);
    REQUIRE(events[161].time_half_dots == start + 1280u);
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

static int dma_restart(void) { return expect_dma_object(0xC0, 1); }

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

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "dma_progress") == 0) return dma_progress();
    if (strcmp(argv[1], "dma_restart") == 0) return dma_restart();
    if (strcmp(argv[1], "dma_source_mapping") == 0) return dma_source_mapping();
    if (strcmp(argv[1], "dma_hram") == 0) return dma_hram();
    if (strcmp(argv[1], "dma_interrupt_stack") == 0) return dma_interrupt_stack();
    if (strcmp(argv[1], "dma_partition") == 0) return dma_partition();
    return 2;
}
