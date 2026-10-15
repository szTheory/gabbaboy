/* Execute the admitted SameSuite DMA ROMs and verify their guest and byte
 * observations against the pinned assembly contract. Private core access is
 * test-only so the oracle can inspect the actual VRAM destination bytes. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef GBB_P13_CORE_SOURCE
#error "This oracle must include the isolated Phase 13 test core"
#endif
#include GBB_P13_CORE_SOURCE

extern void gbb_p12_set_mutants(uint64_t mask);

#define ROM_BYTES 32768u
#define TRACE_CAPACITY 1u
#define OBSERVER_CAPACITY 32768u
#define INITIAL_RESULT_BYTES 32u
#define RUN_SLICE UINT64_C(2048)
#define RUN_BUDGET UINT64_C(1404480)
#define NO_COPY_MASK (UINT64_C(1) << 41)

typedef struct {
    const char *name;
    unsigned blocks;
    unsigned copied_bytes;
    unsigned result_bytes;
    unsigned starts;
    int hblank;
    int checks_mask;
    int checks_status;
} same_case;

static const same_case CASE_GBC_DMA_CONT = {
    "gbc_dma_cont", 2u, 32u, 48u, 2u, 0, 0, 0
};
static const same_case CASE_GDMA_ADDR_MASK = {
    "gdma_addr_mask", 4u, 64u, 64u, 1u, 1, 1, 0
};
static const same_case CASE_HDMA_LCD_OFF = {
    "hdma_lcd_off", 1u, 16u, 40u, 1u, 1, 0, 1
};
static const same_case CASE_HDMA_MODE0 = {
    "hdma_mode0", 1u, 16u, 40u, 1u, 1, 0, 1
};

static const same_case *find_case(const char *name) {
    const same_case *cases[] = {
        &CASE_GBC_DMA_CONT, &CASE_GDMA_ADDR_MASK,
        &CASE_HDMA_LCD_OFF, &CASE_HDMA_MODE0
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i)
        if (strcmp(name, cases[i]->name) == 0) return cases[i];
    return NULL;
}

static int read_rom(const char *path, uint8_t rom[ROM_BYTES]) {
    FILE *file = fopen(path, "rb");
    size_t count;
    int extra;
    if (file == NULL) {
        fprintf(stderr, "samesuite-hdma fixture: cannot open %s\n", path);
        return 0;
    }
    count = fread(rom, 1u, ROM_BYTES, file);
    extra = fgetc(file);
    if (ferror(file) || count != ROM_BYTES || extra != EOF) {
        fprintf(stderr, "samesuite-hdma fixture: expected exactly 32768 bytes\n");
        fclose(file);
        return 0;
    }
    fclose(file);
    return 1;
}

static uint8_t expected_source_byte(uint16_t source, unsigned offset) {
    const uint16_t address = (uint16_t)(source + offset);
    return (offset & 1u) == 0u ? (uint8_t)address : (uint8_t)(address >> 8);
}

static int capture_initial_result(gbb_instance *machine,
                                  const gbb_test_bus_event *events,
                                  size_t event_count,
                                  uint8_t snapshot[INITIAL_RESULT_BYTES],
                                  uint16_t *source, uint16_t *destination,
                                  uint8_t *vram_bank, int *captured) {
    uint8_t regs[4] = {0u, 0u, 0u, 0u};
    for (size_t i = 0u; i < event_count; ++i) {
        const gbb_test_bus_event *event = &events[i];
        if (event->access == 2u && event->address >= 0xFF51u &&
            event->address <= 0xFF54u) {
            regs[event->address - 0xFF51u] = event->value;
        } else if (event->access == 2u && event->address == 0xFF55u) {
            const uint16_t start_source =
                (uint16_t)(((uint16_t)regs[0] << 8) | (regs[1] & 0xF0u));
            const uint16_t start_destination = (uint16_t)(0x8000u |
                ((uint16_t)(regs[2] & 0x1Fu) << 8) | (regs[3] & 0xF0u));
            const unsigned offset = (unsigned)(start_destination - 0x8000u);
            if (start_destination < 0x8000u || start_destination > 0x9FC0u ||
                offset + INITIAL_RESULT_BYTES > GBB_VRAM_BANK_SIZE) {
                fprintf(stderr, "samesuite-hdma initial-result: destination out of range=%04X\n",
                        start_destination);
                return 0;
            }
            *source = start_source;
            *destination = start_destination;
            *vram_bank = machine->vram_bank;
            memcpy(snapshot, &machine->vram[*vram_bank][offset], INITIAL_RESULT_BYTES);
            *captured = 1;
            return 1;
        }
    }
    return 1;
}

static int observe_registers(gbb_instance *machine, const gbb_test_bus_event *events,
                             size_t event_count, const same_case *test,
                             uint16_t *source, uint16_t *destination,
                             uint8_t *last_status) {
    uint8_t regs[4] = {0u, 0u, 0u, 0u};
    unsigned starts = 0u;
    unsigned writes = 0u;
    uint16_t first_source = 0u, first_destination = 0u;
    uint8_t start_values[4] = {0u, 0u, 0u, 0u};
    unsigned status_reads = 0u;
    uint8_t observed_status[4] = {0u, 0u, 0u, 0u};

    for (size_t i = 0u; i < event_count; ++i) {
        const gbb_test_bus_event *event = &events[i];
        if (event->access == 2u && event->address >= 0xFF51u &&
            event->address <= 0xFF54u) {
            regs[event->address - 0xFF51u] = event->value;
        } else if (event->access == 2u && event->address == 0xFF55u) {
            if (starts >= sizeof(start_values)) {
                fprintf(stderr, "samesuite-hdma register predicate: too many FF55 starts\n");
                return 0;
            }
            start_values[starts] = event->value;
            if (starts == 0u) {
                first_source = (uint16_t)(((uint16_t)regs[0] << 8) | (regs[1] & 0xF0u));
                first_destination = (uint16_t)(0x8000u |
                    ((uint16_t)(regs[2] & 0x1Fu) << 8) | (regs[3] & 0xF0u));
            }
            ++starts;
            ++writes;
        } else if (event->access == 1u && event->address == 0xFF55u &&
                   status_reads < sizeof(observed_status)) {
            observed_status[status_reads++] = event->value;
        }
    }

    {
        const unsigned expected_writes = test->starts + (test->checks_status ? 1u : 0u);
        if (writes != expected_writes) {
            fprintf(stderr, "samesuite-hdma register predicate: FF55 writes expected=%u actual=%u\n",
                    expected_writes, writes);
            return 0;
        }
    }
    if (test == &CASE_GBC_DMA_CONT) {
        if (start_values[0] != 0x00u || start_values[1] != 0x00u) {
            fprintf(stderr, "samesuite-hdma register predicate: consecutive GDMA starts changed\n");
            return 0;
        }
    } else if (start_values[0] != 0x83u ||
               (test->checks_status && start_values[1] != 0x00u)) {
        fprintf(stderr, "samesuite-hdma register predicate: HBlank start expected=83 actual=%02X\n",
                start_values[0]);
        return 0;
    }
    if (test->checks_mask &&
        ((regs[1] & 0x0Fu) != 0x0Fu || (regs[3] & 0x0Fu) != 0x0Fu ||
         (first_source & 0x000Fu) != 0u || (first_destination & 0x000Fu) != 0u)) {
        fprintf(stderr, "samesuite-hdma address-mask predicate: raw=%02X/%02X effective=%04X/%04X\n",
                regs[1], regs[3], first_source, first_destination);
        return 0;
    }
    if (first_source < 0xC000u || first_source > 0xDFF0u ||
        first_destination < 0x8000u || first_destination > 0x9FF0u) {
        fprintf(stderr, "samesuite-hdma source/destination predicate: out of allowed WRAM/VRAM window\n");
        return 0;
    }
    if (test->checks_status &&
        (status_reads < 2u || observed_status[0] != 0x02u || observed_status[1] != 0x80u)) {
        fprintf(stderr, "samesuite-hdma FF55 predicate: expected author sequence 02/80 actual=%02X/%02X\n",
                observed_status[0], observed_status[1]);
        return 0;
    }
    *source = first_source;
    *destination = first_destination;
    *last_status = machine->hdma.control_readback;
    if (machine->hdma.mode != 0u || machine->hdma.active != 0u ||
        machine->hdma.pending_hblank != 0u || machine->hdma.blocks_remaining != 0u ||
        machine->hdma.source_cursor != (uint16_t)(first_source + test->copied_bytes) ||
        machine->hdma.destination_cursor != (uint32_t)first_destination + test->copied_bytes ||
        *last_status != (test->checks_status ? 0x80u : 0xFFu)) {
        fprintf(stderr, "samesuite-hdma completion predicate: start=%04X/%04X expected-end=%04X/%05X actual=%04X/%05X FF55=%02X blocks=%u\n",
                first_source, first_destination,
                (uint16_t)(first_source + test->copied_bytes),
                (uint32_t)first_destination + test->copied_bytes,
                machine->hdma.source_cursor, machine->hdma.destination_cursor,
                *last_status, (unsigned)machine->hdma.blocks_remaining);
        return 0;
    }
    return 1;
}

static int run_case(const same_case *test, const char *rom_path, uint64_t mutants,
                    int corrupt_result) {
    uint8_t rom[ROM_BYTES];
    gbb_instance *machine = NULL;
    gbb_test_bus_event *events = NULL;
    gbb_trace_record trace;
    gbb_trace_record registers;
    uint64_t elapsed = 0u;
    uint16_t source = 0u, destination = 0u;
    uint8_t last_status = 0u;
    uint8_t initial_snapshot[INITIAL_RESULT_BYTES] = {0u};
    uint8_t initial_vram_bank = 0u;
    int reached_sentinel = 0;
    int guest_pass = 0;
    int initial_snapshot_captured = 0;

    if (!read_rom(rom_path, rom)) return 2;
    events = calloc(OBSERVER_CAPACITY, sizeof(*events));
    if (events == NULL) {
        fprintf(stderr, "samesuite-hdma observer: bounded allocation failed\n");
        return 2;
    }
    gbb_p12_set_mutants(mutants);
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK || machine == NULL) {
        fprintf(stderr, "samesuite-hdma create: CGB-CPU-E failed\n");
        free(events);
        gbb_destroy(machine);
        return 2;
    }
    if (gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        fprintf(stderr, "samesuite-hdma load: admitted ROM rejected\n");
        free(events);
        gbb_destroy(machine);
        return 2;
    }
    gbb_test_observer_set(machine, events, OBSERVER_CAPACITY);

    while (elapsed < RUN_BUDGET) {
        const uint64_t remaining = RUN_BUDGET - elapsed;
        const uint64_t slice = remaining < RUN_SLICE ? remaining : RUN_SLICE;
        const gbb_run_result run = gbb_run(machine, slice, &trace, TRACE_CAPACITY);
        if (run.consumed_half_dots == 0u || run.consumed_half_dots > slice) {
            fprintf(stderr, "samesuite-hdma run: invalid progress reason=%d consumed=%llu\n",
                    (int)run.reason, (unsigned long long)run.consumed_half_dots);
            free(events);
            gbb_destroy(machine);
            return 2;
        }
        elapsed += run.consumed_half_dots;
        if (!initial_snapshot_captured && !capture_initial_result(machine, events,
                                    gbb_test_observer_count(machine),
                                    initial_snapshot, &source, &destination,
                                    &initial_vram_bank, &initial_snapshot_captured)) {
            free(events);
            gbb_destroy(machine);
            return 1;
        }
        if (run.trace_count == 1u && trace.pc >= 0x0150u && trace.opcode[0] == 0x40u) {
            gbb_test_cpu_snapshot(machine, &registers);
            reached_sentinel = 1;
            break;
        }
        if (run.reason != GBB_STOP_BUDGET && run.reason != GBB_STOP_TRACE_FULL &&
            run.reason != GBB_STOP_HALTED_IDLE) {
            fprintf(stderr, "samesuite-hdma run: unexpected stop=%d at half-dots=%llu\n",
                    (int)run.reason, (unsigned long long)elapsed);
            free(events);
            gbb_destroy(machine);
            return 2;
        }
    }
    if (!reached_sentinel) {
        fprintf(stderr, "samesuite-hdma run: bounded pass sentinel not reached budget=%llu\n",
                (unsigned long long)RUN_BUDGET);
        free(events);
        gbb_destroy(machine);
        return 2;
    }
    guest_pass = registers.b == 3u && registers.c == 5u && registers.d == 8u &&
                 registers.e == 13u && registers.h == 21u && registers.l == 34u &&
                 gbb_peek_ram(machine, 0xCFFEu) == (uint8_t)'P';
    if (!guest_pass) {
        fprintf(stderr, "samesuite-hdma guest-result: expected pass sentinel B..L=03/05/08/0D/15/22 result=P actual=%02X/%02X/%02X/%02X/%02X/%02X result=%02X\n",
                registers.b, registers.c, registers.d, registers.e, registers.h,
                registers.l, gbb_peek_ram(machine, 0xCFFEu));
        free(events);
        gbb_destroy(machine);
        return 1;
    }
    if (!initial_snapshot_captured) {
        fprintf(stderr, "samesuite-hdma initial-result: first FF55 start was not observed\n");
        free(events);
        gbb_destroy(machine);
        return 1;
    }
    if (gbb_test_observer_count(machine) >= OBSERVER_CAPACITY) {
        fprintf(stderr, "samesuite-hdma observer: capacity exhausted\n");
        free(events);
        gbb_destroy(machine);
        return 2;
    }
    if (!observe_registers(machine, events, gbb_test_observer_count(machine), test,
                           &source, &destination, &last_status)) {
        free(events);
        gbb_destroy(machine);
        return 1;
    }
    if (test == &CASE_GDMA_ADDR_MASK) {
        for (unsigned i = 0u; i < INITIAL_RESULT_BYTES; ++i) {
            const uint8_t expected = i < 16u ? expected_source_byte(source, i) : 0u;
            if (initial_snapshot[i] != expected) {
                fprintf(stderr, "samesuite-hdma initial-result: address-mask index=%u expected=%02X actual=%02X source=%04X destination=%04X bank=%u\n",
                        i, expected, initial_snapshot[i], source, destination,
                        (unsigned)initial_vram_bank);
                free(events);
                gbb_destroy(machine);
                return 1;
            }
        }
        if (initial_vram_bank != 0u) {
            fprintf(stderr, "samesuite-hdma initial-result: expected VRAM bank 0 actual=%u\n",
                    (unsigned)initial_vram_bank);
            free(events);
            gbb_destroy(machine);
            return 1;
        }
    }
    {
        const unsigned destination_offset = (unsigned)(destination - 0x8000u);
        if (corrupt_result) machine->vram[0][destination_offset] ^= 0x01u;
        for (unsigned i = 0u; i < test->result_bytes; ++i) {
            uint8_t expected = 0u;
            if (i < test->copied_bytes) expected = expected_source_byte(source, i);
            else if (test->checks_status && i == 32u) expected = 0x02u;
            else if (test->checks_status && i == 33u) expected = 0x80u;
            const uint8_t actual = machine->vram[0][destination_offset + i];
            if (actual != expected) {
                fprintf(stderr, "samesuite-hdma data: %s mismatch index=%u expected=%02X actual=%02X source=%04X destination=%04X\n",
                        corrupt_result ? "corrupted-result" : "guest-data",
                        i, expected, actual, source, destination);
                free(events);
                gbb_destroy(machine);
                return 1;
            }
        }
    }
    printf("samesuite-hdma pass case=%s model=CGB-CPU-E source=%04X destination=%04X blocks=%u ff55=%02X sentinel=03/05/08/0D/15/22 elapsed=%llu\n",
           test->name, source, destination, test->blocks, last_status,
           (unsigned long long)elapsed);
    free(events);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    const same_case *test;
    uint64_t mutants = 0u;
    int corrupt_result = 0;
    const char *rom_path = NULL;
    if (argc < 3) {
        fprintf(stderr, "usage: test_samesuite_hdma <case> <rom> [--mutants MASK] [--corrupt-result]\n");
        return 2;
    }
    test = find_case(argv[1]);
    if (test == NULL) return 2;
    rom_path = argv[2];
    for (int i = 3; i < argc; ++i) {
        if (strcmp(argv[i], "--corrupt-result") == 0) {
            if (corrupt_result) return 2;
            corrupt_result = 1;
        } else if (strcmp(argv[i], "--mutants") == 0 && i + 1 < argc) {
            char *end = NULL;
            const unsigned long long parsed = strtoull(argv[++i], &end, 0);
            if (end == argv[i] || *end != '\0') return 2;
            mutants = (uint64_t)parsed;
        } else {
            return 2;
        }
    }
    if (corrupt_result && (test != &CASE_GBC_DMA_CONT || mutants != 0u)) return 2;
    return run_case(test, rom_path, mutants, corrupt_result);
}
