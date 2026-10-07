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
                                    int probe_cpu_access) {
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

    uint8_t routine[32];
    size_t routine_size = 0;
    routine[routine_size++] = 0x3E; routine[routine_size++] = source_page;
    routine[routine_size++] = 0xE0; routine[routine_size++] = 0x46;
    if (restart) {
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0xD0;
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0x46;
    }
    if (probe_cpu_access) {
        routine[routine_size++] = 0x01; routine[routine_size++] = 0x00;
        routine[routine_size++] = 0xC0; /* LD BC,C000 */
        routine[routine_size++] = 0x0A;  /* blocked CPU read -> A */
        routine[routine_size++] = 0xE0; routine[routine_size++] = 0x90;
        routine[routine_size++] = 0x3E; routine[routine_size++] = 0x77;
        routine[routine_size++] = 0x02;  /* blocked CPU write to C000 */
    }
    routine[routine_size++] = 0x06; routine[routine_size++] = 0x28; /* 40 M-cycles */
    size_t delay_loop = routine_size;
    routine[routine_size++] = 0x05;      /* DEC B */
    routine[routine_size++] = 0x20;
    routine[routine_size++] = 0xFD;      /* JR NZ,DEC B */
    (void)delay_loop;
    routine[routine_size++] = 0x00;      /* two M-cycles past nominal end */
    routine[routine_size++] = 0x00;
    routine[routine_size++] = 0xC3; routine[routine_size++] = 0x00;
    routine[routine_size++] = 0x02;      /* JP 0200 */

    uint16_t source_address = 0;
    emit_copy_to_hram(&main_program, &source_address, routine, routine_size);
    memcpy(rom + 0x150, main_program.bytes, main_program.size);
    memcpy(rom + source_address, routine, routine_size);

    /* After DMA, enable the LCD and halt while one complete frame is produced. */
    size_t post = 0x0200;
    if (probe_cpu_access) {
        rom[post++] = 0xF0; rom[post++] = 0x90; /* LDH A,[90] */
        rom[post++] = 0xEA; rom[post++] = 0x00; rom[post++] = 0xC2;
        rom[post++] = 0xFA; rom[post++] = 0x00; rom[post++] = 0xC0;
        rom[post++] = 0xEA; rom[post++] = 0x01; rom[post++] = 0xC2;
    }
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
        REQUIRE(run.consumed_half_dots != 0);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE || run.reason == GBB_STOP_BUDGET);
        REQUIRE(run.consumed_half_dots <= remaining);
        remaining -= run.consumed_half_dots;
    }
    gbb_frame_info info = {0};
    REQUIRE(gbb_copy_frame(machine, pixels, PIXELS, WIDTH, &info) == GBB_OK);
    REQUIRE(info.width == WIDTH && info.height == HEIGHT && info.generation != 0);
    return 0;
}

static int expect_dma_object(uint8_t source_page, int restart) {
    gbb_instance *machine = load_dma_guest(source_page, restart, 0);
    REQUIRE(machine != NULL);
    uint8_t *pixels = malloc(PIXELS);
    REQUIRE(pixels != NULL);
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(pixels[3] == 3u); /* source byte 0x10 creates OBJ color 1 at x=3 */
    free(pixels);
    gbb_destroy(machine);
    return 0;
}

static int dma_progress(void) { return expect_dma_object(0xC0, 0); }

static int dma_source_mapping(void) {
    static const uint8_t valid_pages[] = {0x80, 0x9F, 0xC0, 0xDF};
    for (size_t i = 0; i < sizeof(valid_pages); ++i)
        REQUIRE(expect_dma_object(valid_pages[i], 0) == 0);
    return 0;
}

static int dma_restart(void) { return expect_dma_object(0xC0, 1); }

static int dma_hram(void) {
    gbb_instance *machine = load_dma_guest(0xC0, 0, 1);
    REQUIRE(machine != NULL);
    uint8_t pixels[PIXELS];
    REQUIRE(run_frame(machine, pixels) == 0);
    REQUIRE(gbb_peek_ram(machine, 0xC200) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC201) == 16u);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "dma_progress") == 0) return dma_progress();
    if (strcmp(argv[1], "dma_restart") == 0) return dma_restart();
    if (strcmp(argv[1], "dma_source_mapping") == 0) return dma_source_mapping();
    if (strcmp(argv[1], "dma_hram") == 0) return dma_hram();
    if (strcmp(argv[1], "dma_partition") == 0) return dma_progress();
    return 2;
}
