#include "../../../src/core/gabbaboy.c"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(const char *why) {
    fprintf(stderr, "FAIL: %s\n", why);
    return 1;
}

static int run_case(unsigned which, int negative) {
    uint8_t rom[32768] = {0};
    rom[0x143] = 0xC0;
    rom[0x147] = 0;
    rom[0x148] = 0;
    rom[0x149] = 0;
    if (which == 0u) {
        rom[0x100] = 0x08; /* LD (a16),SP: two writes at +24 and +32. */
        rom[0x101] = 0x00;
        rom[0x102] = 0xC0;
    } else {
        rom[0x100] = 0xCB; /* RLC (HL): read at +16, write at +24. */
        rom[0x101] = 0x06;
    }
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;

    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &m) != GBB_OK ||
        gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) return fail("create/load");
    m->pc = 0x100u;
    m->sp = 0x1234u;
    m->h = 0xC0u;
    m->l = 0x00u;
    m->wram[0][0] = 0x81u;
    m->lcdc |= 0x80u;
    m->ly = 0u;
    m->ppu_mode = 3u;
    m->ppu_dot = 80u;
    m->ppu_half_phase = 0u;
    m->ppu_transfer_age = which == 0u ? 0u : 4u;
    m->ppu_transfer_complete = 0u;
    m->ppu_output_x = 0u;
    m->ppu_scroll_discard = 0u;
    m->ppu_mode3_stall = 0u;
    m->ppu_fetch_enqueued = 160u;
    m->ppu_fifo_head = 0u;
    m->ppu_fifo_count = negative ? 0u : 1u;
    m->ppu_fifo[0] = UINT8_MAX;

    gbb_test_bus_event bus[64], ppu[64];
    gbb_test_observer_set(m, bus, 64u);
    gbb_test_ppu_observer_set(m, ppu, 64u);
    const uint64_t budget = which == 0u ? 40u : 32u;
    gbb_run_result result = gbb_run(m, budget, NULL, 0u);
    if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots != budget ||
        m->time_half_dots != budget) {
        gbb_destroy(m);
        return fail("run did not preserve current whole-instruction timing");
    }

    uint64_t edge = UINT64_MAX;
    for (size_t i = 0; i < gbb_test_ppu_observer_count(m); ++i) {
        if (ppu[i].address == 0xFF41u && ppu[i].access == 4u && ppu[i].value == 0u)
            edge = ppu[i].time_half_dots;
    }
    size_t relevant = 0;
    uint64_t access_time[4] = {0};
    uint8_t access_kind[4] = {0};
    uint16_t access_address[4] = {0};
    for (size_t i = 0; i < gbb_test_observer_count(m); ++i) {
        if ((bus[i].address == 0xC000u || bus[i].address == 0xC001u) &&
            (bus[i].access == 1u || bus[i].access == 2u)) {
            if (relevant < 4u) {
                access_time[relevant] = bus[i].time_half_dots;
                access_kind[relevant] = bus[i].access;
                access_address[relevant] = bus[i].address;
            }
            ++relevant;
        }
    }

    printf("case=%s negative=%d budget=%llu consumed=%llu master_delta=%llu edge=",
           which == 0u ? "LD_a16_SP" : "CB_RLC_HL", negative,
           (unsigned long long)budget, (unsigned long long)result.consumed_half_dots,
           (unsigned long long)m->time_half_dots);
    if (edge == UINT64_MAX) printf("none"); else printf("%llu", (unsigned long long)edge);
    printf(" accesses=");
    for (size_t i = 0; i < relevant && i < 4u; ++i)
        printf("%s@%llu:%04X", i ? "," : "", (unsigned long long)access_time[i],
               access_address[i]);
    printf("\n");

    if (negative) {
        if (edge != UINT64_MAX || relevant != (which == 0u ? 2u : 2u)) {
            gbb_destroy(m);
            return fail("negative control unexpectedly found edge or lost accesses");
        }
    } else if (which == 0u) {
        if (edge != 26u || relevant != 2u || access_time[0] != 24u ||
            access_time[1] != 32u || access_kind[0] != 2u || access_kind[1] != 2u ||
            access_address[0] != 0xC000u || access_address[1] != 0xC001u) {
            gbb_destroy(m);
            return fail("LD (a16),SP did not place HBlank between its writes");
        }
    } else if (edge != 18u || relevant != 2u || access_time[0] != 16u ||
               access_time[1] != 24u || access_kind[0] != 1u || access_kind[1] != 2u ||
               access_address[0] != 0xC000u || access_address[1] != 0xC000u) {
        gbb_destroy(m);
        return fail("CB RLC (HL) did not place HBlank between its read/write");
    }
    gbb_destroy(m);
    return 0;
}

int main(void) {
    if (run_case(0u, 0) != 0 || run_case(0u, 1) != 0 ||
        run_case(1u, 0) != 0 || run_case(1u, 1) != 0) return 1;
    puts("candidate timelines (model arithmetic, not core HDMA): LD pending boundary: finish at 40 then block [40,104); cursor: HBlank 26, block [26,90), resumed second write at 96, finish 104. CB pending boundary: finish at 32 then block [32,96); cursor: HBlank 18, block [18,82), resumed write at 88, finish 96. Reservation alone preserves late writes, or requires preflight to cost+64 and makes the current budget-sized call no-progress.");
    puts("prototype limit: uses synthetic private PPU state to place a real mode-3-to-0 edge inside real synchronous CPU instructions; it demonstrates the seam and API tradeoff, not CGB silicon steal timing or an implemented DMA scheduler.");
    return 0;
}
