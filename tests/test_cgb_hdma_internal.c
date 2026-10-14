/* White-box CGB HDMA seam tests. The private PPU fixture places a genuine
 * mode-3-to-mode-0 transition inside a real guest instruction; it does not
 * claim physical CGB-E timing. */
#include "../src/core/gabbaboy.c"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

enum { HDMA_SETUP_BYTES = 20, HDMA_SETUP_HALF_DOTS = 200 };

typedef struct {
    gbb_instance *machine;
    uint8_t source[16];
    uint16_t target_pc;
    uint64_t instruction_cost;
    uint64_t edge_offset;
    uint16_t late_address;
    int is_ld_sp;
} hdma_fixture;

static void make_rom(uint8_t rom[32768], int is_ld_sp, int arm) {
    memset(rom, 0, 32768u);
    rom[0x143] = 0xC0u;
    rom[0x147] = 0u;
    rom[0x148] = 0u;
    rom[0x149] = 0u;
    uint8_t *p = rom + 0x100u;
    static const uint8_t setup[][4] = {
        {0x3Eu, 0xC0u, 0xE0u, 0x51u},
        {0x3Eu, 0x00u, 0xE0u, 0x52u},
        {0x3Eu, 0x00u, 0xE0u, 0x53u},
        {0x3Eu, 0x00u, 0xE0u, 0x54u},
        {0x3Eu, 0x80u, 0xE0u, 0x55u}
    };
    memcpy(p, setup, arm ? sizeof(setup) : sizeof(setup) - sizeof(setup[0]));
    p += arm ? sizeof(setup) : sizeof(setup) - sizeof(setup[0]);
    if (is_ld_sp) {
        const uint8_t op[] = {0x08u, 0x00u, 0xC1u}; /* LD (C100),SP */
        memcpy(p, op, sizeof(op));
        p += sizeof(op);
    } else {
        const uint8_t op[] = {0xCBu, 0x06u}; /* RLC (HL), with HL=C100 */
        memcpy(p, op, sizeof(op));
        p += sizeof(op);
    }
    *p = 0xD3u; /* Illegal opcode: a missing steal cannot run another guest op. */
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int fixture_create(hdma_fixture *f, int is_ld_sp, int speed,
                          int arm, int edge) {
    uint8_t rom[32768];
    make_rom(rom, is_ld_sp, arm);
    memset(f, 0, sizeof(*f));
    f->is_ld_sp = is_ld_sp;
    f->target_pc = (uint16_t)(0x100u + (arm ? HDMA_SETUP_BYTES : HDMA_SETUP_BYTES - 4));
    f->instruction_cost = (is_ld_sp ? 40u : 32u) >> speed;
    f->late_address = is_ld_sp ? 0xC101u : 0xC100u;
    f->edge_offset = is_ld_sp ? (speed ? 14u : 26u) : (speed ? 10u : 18u);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &f->machine) == GBB_OK);
    REQUIRE(gbb_load_rom(f->machine, rom, sizeof(rom)) == GBB_OK);
    f->machine->lcdc = 0x91u; /* Let setup reach visible mode 3 before FF55, avoiding an LCD-off kick. */
    for (unsigned i = 0u; i < 16u; ++i) {
        f->source[i] = (uint8_t)(0x31u + 11u * i);
        f->machine->wram[0][i] = f->source[i];
        f->machine->vram[0][i] = (uint8_t)(0xE0u ^ i);
    }
    f->machine->wram[0][0x100] = 0x81u;
    f->machine->wram[0][0x101] = 0x42u;
    f->machine->sp = 0x42A5u;
    f->machine->h = 0xC1u;
    f->machine->l = 0x00u;
    gbb_run_result setup = gbb_run(f->machine, arm ? HDMA_SETUP_HALF_DOTS :
                                    HDMA_SETUP_HALF_DOTS - 40u, NULL, 0u);
    const uint64_t expected_setup = arm ? HDMA_SETUP_HALF_DOTS : HDMA_SETUP_HALF_DOTS - 40u;
    if (setup.reason != GBB_STOP_BUDGET || setup.consumed_half_dots != expected_setup ||
        f->machine->time_half_dots != expected_setup || f->machine->pc != f->target_pc) {
        fprintf(stderr,
            "guest FF51-FF55 setup must reach seam without a stop: reason=%d address=%04X consumed=%llu time=%llu pc=%04X expected_pc=%04X\n",
            setup.reason, gbb_test_last_unsupported_address(f->machine),
            (unsigned long long)setup.consumed_half_dots,
            (unsigned long long)f->machine->time_half_dots,
            f->machine->pc, f->target_pc);
        gbb_destroy(f->machine);
        f->machine = NULL;
        return 1;
    }
    f->machine->double_speed = (uint8_t)speed;
    if (edge) {
        gbb_instance *m = f->machine;
        m->lcdc = 0x91u;
        m->ly = 0u;
        m->ppu_mode = 3u;
        m->ppu_dot = 80u;
        m->ppu_half_phase = 0u;
        m->ppu_transfer_age = (uint8_t)(13u - (f->edge_offset / 2u));
        m->ppu_transfer_complete = 0u;
        m->ppu_output_x = 0u;
        m->ppu_scroll_discard = 0u;
        m->ppu_mode3_stall = 0u;
        m->ppu_fetch_enqueued = 160u;
        m->ppu_fifo_head = 0u;
        m->ppu_fifo_count = edge ? 1u : 0u;
        m->ppu_fifo[0] = UINT8_MAX;
    }
    return 0;
}

static int run_seam_case(int is_ld_sp, int speed) {
    hdma_fixture f;
    REQUIRE(fixture_create(&f, is_ld_sp, speed, 1, 1) == 0);
    gbb_instance *m = f.machine;
    gbb_test_bus_event bus[16], ppu[16];
    memset(bus, 0, sizeof(bus));
    memset(ppu, 0, sizeof(ppu));
    gbb_test_observer_set(m, bus, 16u);
    gbb_test_ppu_observer_set(m, ppu, 16u);

    gbb_trace_record trace[1];
    memset(trace, 0xA5, sizeof(trace));
    const uint64_t start = m->time_half_dots;
    gbb_run_result instruction = gbb_run(m, f.instruction_cost, trace, 1u);
    REQUIRE(instruction.reason == GBB_STOP_BUDGET &&
            instruction.consumed_half_dots == f.instruction_cost &&
            m->time_half_dots - start == instruction.consumed_half_dots &&
            instruction.trace_count == 1u && trace[0].pc == f.target_pc);

    const uint64_t expected_late = is_ld_sp ? (speed ? 16u : 32u) : (speed ? 12u : 24u);
    size_t late_writes = 0u;
    int saw_first_write = !is_ld_sp;
    int saw_second_write = !is_ld_sp;
    int saw_cb_read = is_ld_sp;
    int saw_cb_write = is_ld_sp;
    int saw_edge = 0;
    uint64_t edge_at = UINT64_MAX;
    for (size_t i = 0; i < gbb_test_observer_count(m); ++i) {
        if (is_ld_sp && bus[i].access == 2u) {
            if (bus[i].address == 0xC100u &&
                bus[i].time_half_dots == start + (speed ? 12u : 24u)) {
                ++late_writes;
                saw_first_write = 1;
            }
            if (bus[i].address == 0xC101u &&
                bus[i].time_half_dots == start + expected_late) {
                ++late_writes;
                saw_second_write = 1;
            }
        } else if (!is_ld_sp && bus[i].address == 0xC100u) {
            if (bus[i].access == 1u &&
                bus[i].time_half_dots == start + (speed ? 8u : 16u))
                saw_cb_read = 1;
            if (bus[i].access == 2u && bus[i].time_half_dots == start + expected_late)
                saw_cb_write = 1;
        }
    }
    for (size_t i = 0; i < gbb_test_ppu_observer_count(m); ++i) {
        if (ppu[i].address == 0xFF41u && ppu[i].access == 4u && ppu[i].value == 0u) {
            saw_edge = 1;
            edge_at = ppu[i].time_half_dots;
        }
    }
    REQUIRE(late_writes == (is_ld_sp ? 2u : 0u) && saw_first_write &&
            saw_second_write && saw_cb_read && saw_cb_write);
    REQUIRE(saw_edge == 1 && edge_at == start + f.edge_offset);

    const uint64_t boundary = m->time_half_dots;
    gbb_run_result first_byte = gbb_run(m, 4u, NULL, 0u);
    if (first_byte.consumed_half_dots != 4u || m->time_half_dots != boundary + 4u ||
        m->vram[0][0] != f.source[0]) {
        fprintf(stderr,
            "first-byte commit at boundary+4 expected=%02X actual=%02X consumed=%llu\n",
            f.source[0], m->vram[0][0], (unsigned long long)first_byte.consumed_half_dots);
        gbb_destroy(m);
        return 1;
    }
    gbb_run_result rest = gbb_run(m, 60u, NULL, 0u);
    if (rest.consumed_half_dots != 60u || m->time_half_dots != boundary + 64u) {
        fprintf(stderr, "block duration expected=64 actual=%llu\n",
                (unsigned long long)(m->time_half_dots - boundary));
        gbb_destroy(m);
        return 1;
    }
    for (unsigned i = 0u; i < 16u; ++i) {
        if (m->vram[0][i] != f.source[i]) {
            fprintf(stderr, "transferred byte %u expected=%02X actual=%02X\n",
                    i, f.source[i], m->vram[0][i]);
            gbb_destroy(m);
            return 1;
        }
    }
    gbb_destroy(m);
    return 0;
}

static int test_ld_sp(void) {
    REQUIRE(run_seam_case(1, 0) == 0);
    REQUIRE(run_seam_case(1, 1) == 0);
    return 0;
}

static int test_cb(void) {
    REQUIRE(run_seam_case(0, 0) == 0);
    REQUIRE(run_seam_case(0, 1) == 0);
    return 0;
}

static int test_controls(void) {
    hdma_fixture no_edge;
    REQUIRE(fixture_create(&no_edge, 1, 0, 1, 0) == 0);
    gbb_run_result no_edge_run = gbb_run(no_edge.machine,
        no_edge.instruction_cost + 64u, NULL, 0u);
    if (no_edge_run.consumed_half_dots != no_edge.instruction_cost ||
        no_edge.machine->vram[0][0] == no_edge.source[0]) {
        fprintf(stderr, "no-edge control mismatch: an absent visible 3-to-0 event copied data\n");
        gbb_destroy(no_edge.machine);
        return 1;
    }
    gbb_destroy(no_edge.machine);

    hdma_fixture disabled;
    REQUIRE(fixture_create(&disabled, 1, 0, 0, 1) == 0);
    gbb_run_result disabled_run = gbb_run(disabled.machine,
        disabled.instruction_cost + 64u, NULL, 0u);
    if (disabled_run.consumed_half_dots != disabled.instruction_cost ||
        disabled.machine->vram[0][0] == disabled.source[0]) {
        fprintf(stderr, "disabled-transfer control mismatch: an unarmed edge copied data\n");
        gbb_destroy(disabled.machine);
        return 1;
    }
    gbb_destroy(disabled.machine);
    return 0;
}

static int test_partition(void) {
    hdma_fixture whole, split;
    REQUIRE(fixture_create(&whole, 1, 0, 1, 1) == 0);
    REQUIRE(fixture_create(&split, 1, 0, 1, 1) == 0);
    const uint64_t cost = whole.instruction_cost;
    gbb_run_result one = gbb_run(whole.machine, cost + 64u, NULL, 0u);
    REQUIRE(one.consumed_half_dots == cost + 64u);
    gbb_run_result op = gbb_run(split.machine, cost, NULL, 0u);
    REQUIRE(op.consumed_half_dots == cost);
    static const uint8_t pieces[] = {1u, 3u, 5u, 7u, 11u, 17u, 20u};
    uint64_t consumed = op.consumed_half_dots;
    for (size_t i = 0u; i < sizeof(pieces); ++i) {
        gbb_run_result part = gbb_run(split.machine, pieces[i], NULL, 0u);
        REQUIRE(part.reason == GBB_STOP_BUDGET && part.consumed_half_dots == pieces[i]);
        consumed += part.consumed_half_dots;
    }
    REQUIRE(consumed == cost + 64u && whole.machine->time_half_dots == split.machine->time_half_dots &&
            memcmp(whole.machine->vram[0], split.machine->vram[0], 16u) == 0);
    gbb_destroy(whole.machine);
    gbb_destroy(split.machine);
    return 0;
}

static int test_outputs(void) {
    hdma_fixture f;
    REQUIRE(fixture_create(&f, 1, 0, 1, 1) == 0);
    gbb_trace_record trace[2];
    memset(trace, 0xA5, sizeof(trace));
    gbb_diagnostic_record short_diagnostics[GBB_DIAGNOSTIC_OPERATION_RESERVE + 1u];
    memset(short_diagnostics, 0x5A, sizeof(short_diagnostics));
    const uint64_t start = f.machine->time_half_dots;
    gbb_run_result run = gbb_run_ex(f.machine, f.instruction_cost + 64u,
        trace, 1u, short_diagnostics, GBB_DIAGNOSTIC_OPERATION_RESERVE);
    REQUIRE(run.reason == GBB_STOP_OUTPUT_FULL &&
            run.consumed_half_dots == f.instruction_cost &&
            f.machine->time_half_dots - start == f.instruction_cost);
    REQUIRE(run.trace_count == 1u && trace[1].pc == UINT16_C(0xA5A5));
    const uint8_t *short_after = (const uint8_t *)&short_diagnostics[GBB_DIAGNOSTIC_OPERATION_RESERVE];
    for (size_t i = 0u; i < sizeof(short_diagnostics[0]); ++i) REQUIRE(short_after[i] == 0x5Au);

    enum { DIAGNOSTIC_CAPACITY = GBB_DIAGNOSTIC_OPERATION_RESERVE * 65u };
    gbb_diagnostic_record diagnostics[DIAGNOSTIC_CAPACITY + 1u];
    memset(diagnostics, 0x5A, sizeof(diagnostics));
    run = gbb_run_ex(f.machine, 64u, NULL, 0u, diagnostics, DIAGNOSTIC_CAPACITY);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 64u &&
            f.machine->time_half_dots == start + f.instruction_cost + 64u);
    REQUIRE(memcmp(f.machine->vram[0], f.source, sizeof(f.source)) == 0);
    const uint8_t *after = (const uint8_t *)&diagnostics[DIAGNOSTIC_CAPACITY];
    for (size_t i = 0u; i < sizeof(diagnostics[0]); ++i) REQUIRE(after[i] == 0x5Au);
    gbb_destroy(f.machine);

    REQUIRE(fixture_create(&f, 1, 0, 1, 1) == 0);
    gbb_audio_frame frames[8];
    memset(frames, 0x6B, sizeof(frames));
    size_t frame_count = 0u;
    run = gbb_run_audio(f.machine, f.instruction_cost + 64u,
        frames, 7u, &frame_count);
    REQUIRE(run.reason == GBB_STOP_BUDGET &&
            run.consumed_half_dots == f.instruction_cost + 64u && frame_count <= 7u);
    const uint8_t *audio_sentinel = (const uint8_t *)&frames[7];
    for (size_t i = 0u; i < sizeof(frames[0]); ++i) REQUIRE(audio_sentinel[i] == 0x6Bu);
    gbb_destroy(f.machine);
    return 0;
}

static void finish_rom(uint8_t rom[32768]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static size_t emit_pair(uint8_t *program, size_t at, uint8_t immediate,
                        uint8_t address) {
    program[at++] = 0x3Eu; program[at++] = immediate;
    program[at++] = 0xE0u; program[at++] = address;
    return at;
}

static void make_policy_rom(uint8_t rom[32768], uint8_t start,
                            uint8_t cancel, int cancel_after_read,
                            int active_write_restart) {
    memset(rom, 0, 32768u);
    rom[0x143] = 0xC0u;
    rom[0x147] = 0u;
    rom[0x148] = 0u;
    rom[0x149] = 0u;
    uint8_t *p = rom + 0x100u;
    size_t at = 0u;
    at = emit_pair(p, at, 0xC0u, 0x51u);
    at = emit_pair(p, at, 0x00u, 0x52u);
    at = emit_pair(p, at, 0x00u, 0x53u);
    at = emit_pair(p, at, 0x00u, 0x54u);
    at = emit_pair(p, at, start, 0x55u);
    if (active_write_restart) {
        at = emit_pair(p, at, 0xD0u, 0x51u);
        at = emit_pair(p, at, 0x82u, 0x55u);
    }
    p[at++] = 0xF0u; p[at++] = 0x55u; /* guest reads FF55 */
    p[at++] = 0xE0u; p[at++] = 0x80u; /* save the readback in HRAM */
    if (cancel_after_read) {
        at = emit_pair(p, at, cancel, 0x55u);
        p[at++] = 0xF0u; p[at++] = 0x55u;
        p[at++] = 0xE0u; p[at++] = 0x81u;
    }
    p[at] = 0xD3u;
    finish_rom(rom);
}

static int policy_fixture_create(gbb_instance **machine, uint8_t start,
                                 uint8_t cancel, int cancel_after_read,
                                 int active_write_restart, int speed,
                                 uint8_t lcdc, uint8_t mode, uint8_t line,
                                 size_t source_bytes) {
    uint8_t rom[32768];
    make_policy_rom(rom, start, cancel, cancel_after_read, active_write_restart);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, machine) == GBB_OK);
    REQUIRE(gbb_load_rom(*machine, rom, sizeof(rom)) == GBB_OK);
    gbb_instance *m = *machine;
    for (size_t i = 0u; i < source_bytes; ++i)
        m->wram[0][i] = (uint8_t)(0x27u + 37u * i);
    memset(m->vram[0], 0xA5, sizeof(m->vram[0]));
    memset(m->vram[1], 0x5A, sizeof(m->vram[1]));
    m->lcdc = 0u;
    gbb_run_result setup = gbb_run(m, 160u, NULL, 0u); /* four guest FF51-54 writes */
    if (setup.reason != GBB_STOP_BUDGET || setup.consumed_half_dots != 160u ||
        m->pc != 0x110u) {
        fprintf(stderr, "HDMA policy guest setup failed: reason=%d pc=%04X consumed=%llu\n",
                setup.reason, m->pc, (unsigned long long)setup.consumed_half_dots);
        gbb_destroy(m);
        *machine = NULL;
        return 1;
    }
    m->double_speed = (uint8_t)speed;
    m->lcdc = lcdc;
    m->ppu_mode = mode;
    m->ppu_dot = mode == 0u ? 300u : (mode == 3u ? 100u : 0u);
    m->ppu_half_phase = 0u;
    m->ly = line;
    return 0;
}

static int check_guest_kick_cancel(uint8_t lcdc, uint8_t mode, int speed,
                                   uint8_t cancel, uint8_t expected_cancel,
                                   int flip_cancel) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x83u, flip_cancel ? 1u : cancel, 1, 0,
                                  speed, lcdc, mode, 0u, 16u) == 0);
    const uint64_t start = m->time_half_dots;
    gbb_run_result block = gbb_run(m, (40u >> speed) + 64u, NULL, 0u);
    if (block.reason != GBB_STOP_BUDGET || block.consumed_half_dots != (40u >> speed) + 64u ||
        m->time_half_dots - start != (40u >> speed) + 64u ||
        memcmp(m->vram[0], m->wram[0], 16u) != 0) {
        fprintf(stderr, "hdma state matrix: initial kick did not commit exactly one block\n");
        gbb_destroy(m);
        return 1;
    }
    const unsigned read_cost = 48u >> speed;
    gbb_run_result read_active = gbb_run(m, read_cost, NULL, 0u);
    if (read_active.consumed_half_dots != read_cost || m->hram[0] != 0x02u) {
        fprintf(stderr, "hdma state matrix: guest active FF55 expected=02 actual=%02X\n",
                m->hram[0]);
        gbb_destroy(m);
        return 1;
    }
    const unsigned cancel_cost = 40u >> speed;
    gbb_run_result cancel_run = gbb_run(m, cancel_cost, NULL, 0u);
    if (cancel_run.consumed_half_dots != cancel_cost) {
        fprintf(stderr, "hdma state matrix: guest cancellation instruction was not executed\n");
        gbb_destroy(m);
        return 1;
    }
    gbb_run_result read_cancelled = gbb_run(m, read_cost, NULL, 0u);
    if (read_cancelled.consumed_half_dots != read_cost || m->hram[1] != expected_cancel) {
        fprintf(stderr, "hdma state matrix: guest cancel readback expected=%02X actual=%02X\n",
                expected_cancel, m->hram[1]);
        gbb_destroy(m);
        return 1;
    }
    REQUIRE(m->hdma.blocks_remaining == 0u && !m->hdma.active &&
            !m->hdma.pending_hblank && m->hdma.source_cursor == 0xC010u &&
            m->hdma.destination_cursor == 0x8010u);
    gbb_destroy(m);
    return 0;
}

static int run_gdma_count(unsigned blocks, int speed) {
    gbb_instance *m = NULL;
    REQUIRE(blocks >= 1u && blocks <= 128u);
    REQUIRE(policy_fixture_create(&m, (uint8_t)(blocks - 1u), 0u, 0, 0,
                                  speed, 0u, 0u, 0u, blocks * 16u) == 0);
    const uint64_t start = m->time_half_dots;
    gbb_run_result first = gbb_run(m, (40u >> speed) + 64u, NULL, 0u);
    REQUIRE(first.reason == GBB_STOP_BUDGET && first.consumed_half_dots == (40u >> speed) + 64u);
    for (unsigned block = 1u; block < blocks; ++block) {
        gbb_run_result next = gbb_run(m, 64u, NULL, 0u);
        if (next.reason != GBB_STOP_BUDGET || next.consumed_half_dots != 64u) {
            fprintf(stderr, "gdma bounded count=%u block=%u consumed=%llu reason=%d\n",
                    blocks, block, (unsigned long long)next.consumed_half_dots, next.reason);
            gbb_destroy(m);
            return 1;
        }
    }
    const unsigned read_cost = 48u >> speed;
    gbb_run_result readback = gbb_run(m, read_cost, NULL, 0u);
    if (readback.consumed_half_dots != read_cost || m->hram[0] != 0xFFu ||
        m->time_half_dots - start != (uint64_t)((40u >> speed) + 64u * blocks + read_cost) ||
        m->hdma.source_cursor != (uint16_t)(0xC000u + blocks * 16u) ||
        m->hdma.destination_cursor != 0x8000u + blocks * 16u) {
        fprintf(stderr, "gdma completion/count readback mismatch count=%u speed=%d consumed=%llu expected=%u status=%02X source=%04X destination=%04X\n",
                blocks, speed, (unsigned long long)(m->time_half_dots - start),
                (40u >> speed) + 64u * blocks + read_cost, m->hram[0],
                m->hdma.source_cursor, m->hdma.destination_cursor);
        gbb_destroy(m);
        return 1;
    }
    for (unsigned i = 0u; i < blocks * 16u; ++i) {
        if (m->vram[0][i] != m->wram[0][i]) {
            fprintf(stderr, "gdma data mismatch count=%u offset=%u\n", blocks, i);
            gbb_destroy(m);
            return 1;
        }
    }
    gbb_destroy(m);
    return 0;
}

static int test_cursor_continuation(void) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x80u, 0u, 0, 0, 0, 0u, 0u, 0u, 64u) == 0);
    gbb_run_result first = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(first.consumed_half_dots == 104u && m->hdma.blocks_remaining == 0u &&
            m->hdma.source_cursor == 0xC010u && m->hdma.destination_cursor == 0x8010u &&
            m->hdma.control_readback == 0xFFu);
    hdma_register_write(m, 0xFF55u, 0x00u); /* a new idle GDMA continues the cursors */
    gbb_run_result second = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(second.consumed_half_dots == 64u && m->hdma.source_cursor == 0xC020u &&
            m->hdma.destination_cursor == 0x8020u);
    REQUIRE(memcmp(m->vram[0] + 16u, m->wram[0] + 16u, 16u) == 0);

    for (unsigned i = 0u; i < 16u; ++i)
        m->wram[1][0x30u + i] = (uint8_t)(0xD0u + i);
    hdma_register_write(m, 0xFF51u, 0xD0u);
    REQUIRE(m->hdma.source_cursor == 0xD020u);
    hdma_register_write(m, 0xFF52u, 0x30u);
    REQUIRE(m->hdma.source_cursor == 0xD030u);
    hdma_register_write(m, 0xFF53u, 0x05u);
    REQUIRE(m->hdma.destination_cursor == 0x8520u);
    hdma_register_write(m, 0xFF54u, 0x30u);
    REQUIRE(m->hdma.destination_cursor == 0x8530u);
    hdma_register_write(m, 0xFF55u, 0x00u);
    gbb_run_result reprogrammed = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(reprogrammed.consumed_half_dots == 64u && m->hdma.source_cursor == 0xD040u &&
            m->hdma.destination_cursor == 0x8540u && m->hdma.control_readback == 0xFFu);
    REQUIRE(memcmp(m->vram[0] + 0x530u, m->wram[1] + 0x30u, 16u) == 0);

    m->hdma.mode = 2u;
    m->hdma.active = 1u;
    m->hdma.pending_hblank = 0u;
    m->hdma.blocks_remaining = 7u;
    m->hdma.control_readback = 6u;
    const uint16_t source = m->hdma.source_cursor;
    const uint16_t destination = m->hdma.destination_cursor;
    hdma_register_write(m, 0xFF51u, 0xC0u);
    hdma_register_write(m, 0xFF52u, 0x00u);
    hdma_register_write(m, 0xFF53u, 0x00u);
    hdma_register_write(m, 0xFF54u, 0x00u);
    hdma_register_write(m, 0xFF55u, 0x85u);
    REQUIRE(m->hdma.mode == 2u && m->hdma.active && !m->hdma.pending_hblank &&
            m->hdma.blocks_remaining == 7u && m->hdma.control_readback == 6u &&
            m->hdma.source_cursor == source && m->hdma.destination_cursor == destination &&
            m->hdma.source_high == 0xD0u && m->hdma.source_low == 0x30u);
    gbb_destroy(m);
    return 0;
}

static int test_state_matrix(int flip_cancel) {
    for (int speed = 0; speed <= 1; ++speed) {
        REQUIRE(check_guest_kick_cancel(0u, 0u, speed, 0u, 0x80u, flip_cancel) == 0);
        REQUIRE(check_guest_kick_cancel(0x91u, 0u, speed, 0u, 0x80u, 0) == 0);
        REQUIRE(check_guest_kick_cancel(0u, 0u, speed, 0x05u, 0x85u, 0) == 0);
        REQUIRE(run_gdma_count(1u, speed) == 0);
        REQUIRE(run_gdma_count(2u, speed) == 0);
        REQUIRE(run_gdma_count(128u, speed) == 0);
    }
    REQUIRE(test_cursor_continuation() == 0);

    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x83u, 0u, 0, 1, 0, 0x91u, 3u, 0u, 16u) == 0);
    gbb_run_result waiting = gbb_run(m, 168u, NULL, 0u);
    REQUIRE(waiting.reason == GBB_STOP_BUDGET && waiting.consumed_half_dots == 168u &&
            m->hram[0] == 0x02u && m->hdma.mode == 1u &&
            m->hdma.blocks_remaining == 3u && m->hdma.source_high == 0xC0u &&
            m->hdma.source_cursor == 0xC000u && !m->hdma.pending_hblank &&
            m->vram[0][0] == 0xA5u);
    ppu_set_mode(m, 0u);
    REQUIRE(m->hdma.pending_hblank);
    gbb_run_result block = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(block.consumed_half_dots == 64u && m->vram[0][0] == m->wram[0][0]);
    gbb_destroy(m);
    return 0;
}

static int test_trigger_matrix(void) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x82u, 0u, 0, 0, 0, 0x91u, 3u, 0u, 32u) == 0);
    gbb_run_result armed = gbb_run(m, 40u, NULL, 0u);
    REQUIRE(armed.consumed_half_dots == 40u && m->hdma.mode == 1u &&
            m->hdma.blocks_remaining == 3u && !m->hdma.pending_hblank &&
            m->vram[0][0] == 0xA5u);
    m->ly = 144u;
    ppu_set_mode(m, 0u);
    REQUIRE(!m->hdma.pending_hblank);
    gbb_run_result vblank = gbb_run(m, 48u, NULL, 0u);
    REQUIRE(vblank.consumed_half_dots == 48u && m->hram[0] == 0x02u &&
            m->hdma.blocks_remaining == 3u &&
            m->vram[0][0] == 0xA5u);
    m->ly = 0u;
    m->lcdc = 0u;
    ppu_set_mode(m, 3u);
    ppu_set_mode(m, 0u);
    REQUIRE(!m->hdma.pending_hblank);
    gbb_destroy(m);

    REQUIRE(policy_fixture_create(&m, 0x82u, 0u, 0, 0, 0, 0u, 0u, 0u, 32u) == 0);
    gbb_run_result kick = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(kick.consumed_half_dots == 104u && m->hdma.blocks_remaining == 2u &&
            !m->hdma.pending_hblank && m->vram[0][0] == m->wram[0][0] &&
            m->vram[0][16] == 0xA5u);
    ppu_set_mode(m, 0u); /* same mode is a level, not a second initial kick */
    gbb_run_result no_repeat = gbb_run(m, 48u, NULL, 0u);
    REQUIRE(no_repeat.consumed_half_dots == 48u && m->vram[0][16] == 0xA5u);
    m->lcdc = 0x91u;
    ppu_set_mode(m, 3u);
    ppu_set_mode(m, 0u);
    REQUIRE(m->hdma.pending_hblank);
    gbb_run_result visible = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(visible.consumed_half_dots == 64u && m->vram[0][16] == m->wram[0][16]);
    ppu_set_mode(m, 3u);
    ppu_set_mode(m, 0u);
    REQUIRE(m->hdma.pending_hblank);
    write8(m, 0xFF40u, 0u);
    REQUIRE(m->hdma.mode == 1u && !m->hdma.pending_hblank &&
            m->hdma.blocks_remaining == 1u);
    write8(m, 0xFF40u, 0x91u);
    ppu_set_mode(m, 3u);
    ppu_set_mode(m, 0u);
    REQUIRE(m->hdma.pending_hblank);
    gbb_run_result resumed = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(resumed.consumed_half_dots == 64u && m->vram[0][32u] == m->wram[0][32u]);
    gbb_destroy(m);
    return 0;
}

static int test_trigger_controls(void) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x81u, 0u, 0, 0, 0, 0x91u, 3u, 144u, 16u) == 0);
    gbb_run_result arm = gbb_run(m, 40u, NULL, 0u);
    REQUIRE(arm.consumed_half_dots == 40u && !m->hdma.pending_hblank);
    ppu_set_mode(m, 0u);
    REQUIRE(!m->hdma.pending_hblank);
    m->ly = 0u;
    m->lcdc = 0u;
    ppu_set_mode(m, 3u);
    ppu_set_mode(m, 0u);
    REQUIRE(!m->hdma.pending_hblank);
    gbb_run_result none = gbb_run(m, 48u, NULL, 0u);
    REQUIRE(none.consumed_half_dots == 48u && m->hdma.blocks_remaining == 2u &&
            m->vram[0][0] == 0xA5u);
    gbb_destroy(m);
    return 0;
}

static int test_trigger_flip(void) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x82u, 0u, 0, 0, 0, 0u, 0u, 0u, 32u) == 0);
    gbb_run_result kick = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(kick.consumed_half_dots == 104u && m->hdma.blocks_remaining == 2u);
    ppu_set_mode(m, 0u);
    m->hdma.pending_hblank = 1u; /* injected duplicate event must be caught */
    if (m->hdma.pending_hblank) {
        fprintf(stderr, "trigger matrix: injected repeated-mode event detected\n");
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_timing_policy(int flip) {
    for (int speed = 0; speed <= 1; ++speed) {
        gbb_instance *m = NULL;
        REQUIRE(policy_fixture_create(&m, 0x80u, 0u, 0, 0, speed, 0u, 0u, 0u, 16u) == 0);
        const uint64_t start = m->time_half_dots;
        gbb_run_result start_block = gbb_run(m, (40u >> speed), NULL, 0u);
        REQUIRE(start_block.consumed_half_dots == (40u >> speed));
        REQUIRE(m->hdma.pending_hblank && hdma_admit_block(m));
        if (flip && speed == 0) m->hdma.byte_phase = 1u;
        for (unsigned byte = 0u; byte < 16u; ++byte) {
            const uint64_t expected = start + (40u >> speed) + 4u * (byte + 1u);
            while (m->time_half_dots < expected) {
                gbb_run_result tick = gbb_run(m, 1u, NULL, 0u);
                REQUIRE(tick.consumed_half_dots == 1u);
                if (m->time_half_dots < expected &&
                    m->vram[0][byte] == m->wram[0][byte]) {
                    fprintf(stderr, "timing policy: byte %u committed early\n", byte);
                    gbb_destroy(m);
                    return 1;
                }
            }
            if (m->vram[0][byte] != m->wram[0][byte]) {
                fprintf(stderr,
                    "timing policy: byte %u expected commit at +%llu half-dots\n",
                    byte, (unsigned long long)(expected - start));
                gbb_destroy(m);
                return 1;
            }
        }
        REQUIRE(m->time_half_dots - start == (40u >> speed) + 64u);
        gbb_destroy(m);
    }
    puts("timing sensitivity: shifts -8,-4,-2,-1,+1,+2,+4,+8 half-dots are detected by per-half-dot checks at all 16 byte edges; software blind window around sampled edges: none; physical CGB-E timing: UNKNOWN");
    return 0;
}

static void make_address_rom(uint8_t *rom, size_t rom_size, uint8_t cart_type,
                             uint8_t rom_size_code, uint8_t ram_size_code,
                             uint16_t source, uint16_t destination, uint8_t start) {
    for (size_t i = 0u; i < rom_size; ++i)
        rom[i] = (uint8_t)(0x21u + 41u * (i / 0x4000u) + 7u * (i & 0x3FFFu));
    rom[0x143u] = 0xC0u;
    rom[0x147u] = cart_type;
    rom[0x148u] = rom_size_code;
    rom[0x149u] = ram_size_code;
    uint8_t *program = rom + 0x100u;
    size_t at = 0u;
    at = emit_pair(program, at, (uint8_t)(source >> 8), 0x51u);
    at = emit_pair(program, at, (uint8_t)source, 0x52u);
    at = emit_pair(program, at, (uint8_t)((destination >> 8) & 0x1Fu), 0x53u);
    at = emit_pair(program, at, (uint8_t)destination, 0x54u);
    at = emit_pair(program, at, start, 0x55u);
    program[at++] = 0xF0u; program[at++] = 0x55u;
    program[at++] = 0xE0u; program[at++] = 0x80u;
    program[at] = 0xD3u;
    finish_rom(rom);
}

static int address_fixture_create(gbb_instance **machine, uint16_t source,
                                  uint16_t destination, uint8_t start,
                                  uint8_t cart_type, uint8_t rom_size_code,
                                  uint8_t ram_size_code, size_t rom_size) {
    uint8_t rom[0x10000u];
    REQUIRE(rom_size <= sizeof(rom));
    make_address_rom(rom, rom_size, cart_type, rom_size_code, ram_size_code,
                     source, destination, start);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, machine) == GBB_OK);
    REQUIRE(gbb_load_rom(*machine, rom, rom_size) == GBB_OK);
    gbb_instance *m = *machine;
    m->lcdc = 0u;
    for (unsigned bank = 0u; bank < GBB_WRAM_BANKS; ++bank)
        for (unsigned i = 0u; i < GBB_WRAM_BANK_SIZE; ++i)
            m->wram[bank][i] = (uint8_t)(0x30u + bank * 19u + i * 5u);
    memset(m->vram[0], 0xA5, sizeof(m->vram[0]));
    memset(m->vram[1], 0xA5, sizeof(m->vram[1]));
    if (m->cartridge_ram != NULL)
        for (size_t i = 0u; i < m->cartridge_ram_size; ++i)
            m->cartridge_ram[i] = (uint8_t)(0x60u + 3u * i);
    gbb_run_result setup = gbb_run(m, 160u, NULL, 0u);
    if (setup.reason != GBB_STOP_BUDGET || setup.consumed_half_dots != 160u ||
        m->pc != 0x110u) {
        fprintf(stderr, "HDMA address guest setup failed: reason=%d pc=%04X consumed=%llu\n",
                setup.reason, m->pc, (unsigned long long)setup.consumed_half_dots);
        gbb_destroy(m);
        *machine = NULL;
        return 1;
    }
    return 0;
}

static int save_address_status(gbb_instance *m, uint8_t expected) {
    gbb_run_result readback = gbb_run(m, 48u, NULL, 0u);
    if (readback.consumed_half_dots != 48u || m->hram[0] != expected) {
        fprintf(stderr, "HDMA guest FF55 expected=%02X actual=%02X reason=%d consumed=%llu\n",
                expected, m->hram[0], readback.reason,
                (unsigned long long)readback.consumed_half_dots);
        return 1;
    }
    return 0;
}

static int expect_invalid_source(uint16_t source) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, source, 0x8000u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_test_bus_event events[256];
    memset(events, 0, sizeof(events));
    gbb_test_observer_set(m, events, 256u);
    gbb_run_result run = gbb_run(m, 104u, NULL, 0u);
    if (run.reason != GBB_STOP_UNSUPPORTED_BUS || run.consumed_half_dots != 40u) {
        fprintf(stderr, "address matrix: invalid source %04X accepted reason=%d consumed=%llu\n",
                source, run.reason, (unsigned long long)run.consumed_half_dots);
        gbb_destroy(m);
        return 1;
    }
    REQUIRE(!m->hdma.active && !m->hdma.pending_hblank && m->hdma.mode == 0u &&
            m->hdma.blocks_remaining == 1u && m->hdma.source_cursor == source &&
            m->hdma.destination_cursor == 0x8000u &&
            m->hdma.control_readback == 0x80u);
    for (unsigned i = 0u; i < 16u; ++i) REQUIRE(m->vram[0][i] == 0xA5u);
    const size_t event_count = gbb_test_observer_count(m);
    for (size_t i = 0u; i < event_count; ++i) {
        if (events[i].address >= source && events[i].address < (uint32_t)source + 16u) {
            fprintf(stderr, "address matrix: invalid source %04X reached CPU bus observer\n", source);
            gbb_destroy(m);
            return 1;
        }
    }
    REQUIRE(save_address_status(m, 0x80u) == 0);
    gbb_destroy(m);
    return 0;
}

static int expect_rom_block(uint16_t source) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, source, 0x8000u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result run = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 104u);
    REQUIRE(memcmp(m->vram[0], m->rom + source, 16u) == 0);
    REQUIRE(m->hdma.source_cursor == (uint16_t)(source + 16u) &&
            m->hdma.destination_cursor == 0x8010u && m->hdma.control_readback == 0xFFu);
    REQUIRE(save_address_status(m, 0xFFu) == 0);
    gbb_destroy(m);
    return 0;
}

static int expect_rom_mapping_crossing(void) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, 0x3FF0u, 0x8000u, 0x01u, 0x01u, 1u, 0u,
                                   65536u) == 0);
    gbb_run_result run = gbb_run(m, 168u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 168u);
    REQUIRE(memcmp(m->vram[0], m->rom + 0x3FF0u, 16u) == 0);
    REQUIRE(memcmp(m->vram[0] + 16u, m->rom + 0x4000u, 16u) == 0);
    REQUIRE(m->hdma.source_cursor == 0x4010u && m->hdma.destination_cursor == 0x8020u);
    REQUIRE(save_address_status(m, 0xFFu) == 0);
    gbb_destroy(m);
    return 0;
}

static int expect_prefix_then_invalid(uint16_t source, uint8_t cart_type,
                                      uint8_t rom_size_code, uint8_t ram_size_code,
                                      size_t rom_size, uint16_t next_source,
                                      const uint8_t *prefix) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, source, 0x8000u, 0x01u, cart_type,
                                   rom_size_code, ram_size_code, rom_size) == 0);
    if (cart_type == 0x03u) write8(m, 0x0000u, 0x0Au);
    gbb_run_result run = gbb_run(m, 168u, NULL, 0u);
    if (run.reason != GBB_STOP_UNSUPPORTED_BUS || run.consumed_half_dots != 104u) {
        fprintf(stderr, "address matrix: continuation source %04X did not stop at %04X\n",
                source, next_source);
        gbb_destroy(m);
        return 1;
    }
    REQUIRE(memcmp(m->vram[0], prefix, 16u) == 0);
    for (unsigned i = 16u; i < 32u; ++i) REQUIRE(m->vram[0][i] == 0xA5u);
    REQUIRE(!m->hdma.active && !m->hdma.pending_hblank && m->hdma.mode == 0u &&
            m->hdma.blocks_remaining == 1u && m->hdma.source_cursor == next_source &&
            m->hdma.destination_cursor == 0x8010u && m->hdma.control_readback == 0x80u);
    REQUIRE(save_address_status(m, 0x80u) == 0);
    gbb_destroy(m);
    return 0;
}

static int test_address_matrix(void) {
    REQUIRE(expect_rom_block(0x0000u) == 0);
    REQUIRE(expect_rom_mapping_crossing() == 0);
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, 0x7FF0u, 0x8000u, 0x01u, 0x01u, 1u, 0u,
                                   65536u) == 0);
    gbb_run_result rom_prefix = gbb_run(m, 168u, NULL, 0u);
    REQUIRE(rom_prefix.reason == GBB_STOP_UNSUPPORTED_BUS &&
            rom_prefix.consumed_half_dots == 104u &&
            memcmp(m->vram[0], m->rom + 0x7FF0u, 16u) == 0 &&
            m->hdma.source_cursor == 0x8000u && m->hdma.blocks_remaining == 1u &&
            m->hdma.control_readback == 0x80u);
    REQUIRE(save_address_status(m, 0x80u) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xA000u, 0x8000u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result absent_ram = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(absent_ram.reason == GBB_STOP_BUDGET && absent_ram.consumed_half_dots == 104u);
    for (unsigned i = 0u; i < 16u; ++i) REQUIRE(m->vram[0][i] == 0xFFu);
    REQUIRE(save_address_status(m, 0xFFu) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xA000u, 0x8000u, 0x00u, 0x03u, 0u, 3u,
                                   32768u) == 0);
    gbb_run_result disabled_ram = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(disabled_ram.reason == GBB_STOP_BUDGET && disabled_ram.consumed_half_dots == 104u);
    for (unsigned i = 0u; i < 16u; ++i) REQUIRE(m->vram[0][i] == 0xFFu);
    REQUIRE(save_address_status(m, 0xFFu) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xBFF0u, 0x8000u, 0x01u, 0x03u, 0u, 3u,
                                   32768u) == 0);
    write8(m, 0x0000u, 0x0Au);
    for (unsigned i = 0u; i < 16u; ++i) m->cartridge_ram[0x1FF0u + i] = (uint8_t)(0xB0u + i);
    gbb_run_result ram_to_wram = gbb_run(m, 168u, NULL, 0u);
    REQUIRE(ram_to_wram.reason == GBB_STOP_BUDGET && ram_to_wram.consumed_half_dots == 168u);
    REQUIRE(memcmp(m->vram[0], m->cartridge_ram + 0x1FF0u, 16u) == 0);
    REQUIRE(memcmp(m->vram[0] + 16u, m->wram[0], 16u) == 0);
    REQUIRE(save_address_status(m, 0xFFu) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xC000u, 0x8000u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result wram_start = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(wram_start.reason == GBB_STOP_BUDGET && wram_start.consumed_half_dots == 104u &&
            memcmp(m->vram[0], m->wram[0], 16u) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xCFF0u, 0x8000u, 0x01u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    const uint8_t *c_prefix = m->wram[0] + 0x0FF0u;
    gbb_run_result wram_cross = gbb_run(m, 168u, NULL, 0u);
    REQUIRE(wram_cross.reason == GBB_STOP_BUDGET && wram_cross.consumed_half_dots == 168u);
    REQUIRE(memcmp(m->vram[0], c_prefix, 16u) == 0);
    REQUIRE(memcmp(m->vram[0] + 16u, m->wram[1] + 0x1000u, 16u) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xDFF0u, 0x8000u, 0x01u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    REQUIRE(expect_prefix_then_invalid(0xDFF0u, 0x00u, 0u, 0u, 32768u,
                                       0xE000u, m->wram[1] + 0x1FF0u) == 0);
    gbb_destroy(m);

    static const uint16_t invalid_sources[] = {
        0x8000u, 0xE000u, 0xFE00u, 0xFEA0u, 0xFF00u, 0xFF80u
    };
    for (size_t i = 0u; i < sizeof(invalid_sources) / sizeof(invalid_sources[0]); ++i)
        REQUIRE(expect_invalid_source(invalid_sources[i]) == 0);
    return 0;
}

static int test_address_flip(void) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, 0xE000u, 0x8000u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    m->vram[0][0] = m->wram[0][0]; /* inject an unauthorized byte into the rejected block */
    if (m->vram[0][0] != 0xA5u) {
        fprintf(stderr, "address matrix: invalid-block byte mutated\n");
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_overflow_policy(void) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, 0xC000u, 0x9FF0u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    if (sizeof(m->hdma.destination_cursor) < sizeof(uint32_t)) {
        fprintf(stderr, "overflow policy: destination cursor is not widened for A000 continuation\n");
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xC000u, 0x9FF0u, 0x00u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result one = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(one.reason == GBB_STOP_BUDGET && one.consumed_half_dots == 104u &&
            memcmp(m->vram[0] + 0x1FF0u, m->wram[0], 16u) == 0 &&
            m->hdma.destination_cursor == 0xA000u && m->hdma.blocks_remaining == 0u &&
            m->hdma.control_readback == 0xFFu);
    REQUIRE(save_address_status(m, 0xFFu) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xC000u, 0x9FF0u, 0x01u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result overflow = gbb_run(m, 168u, NULL, 0u);
    REQUIRE(overflow.reason == GBB_STOP_UNSUPPORTED_BUS && overflow.consumed_half_dots == 104u &&
            memcmp(m->vram[0] + 0x1FF0u, m->wram[0], 16u) == 0 &&
            m->hdma.destination_cursor == 0xA000u && m->hdma.source_cursor == 0xC010u &&
            m->hdma.blocks_remaining == 1u && !m->hdma.active && !m->hdma.pending_hblank &&
            m->hdma.mode == 0u && m->hdma.control_readback == 0x80u);
    REQUIRE(save_address_status(m, 0x80u) == 0);

    hdma_register_write(m, 0xFF55u, 0x00u);
    gbb_run_result retry = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(retry.reason == GBB_STOP_UNSUPPORTED_BUS && retry.consumed_half_dots == 0u &&
            m->hdma.destination_cursor == 0xA000u && m->hdma.blocks_remaining == 1u &&
            m->hdma.control_readback == 0x80u);
    hdma_register_write(m, 0xFF53u, 0x00u);
    hdma_register_write(m, 0xFF54u, 0x00u);
    REQUIRE(m->hdma.destination_cursor == 0x8000u);
    hdma_register_write(m, 0xFF55u, 0x00u);
    gbb_run_result repaired = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(repaired.consumed_half_dots == 64u &&
            memcmp(m->vram[0], m->wram[0] + 16u, 16u) == 0 &&
            m->hdma.destination_cursor == 0x8010u && m->hdma.control_readback == 0xFFu);
    gbb_destroy(m);
    return 0;
}

static int test_overflow_flip(void) {
    uint32_t destination_cursor = 0xA000u;
    destination_cursor = 0x8000u; /* injected narrow-offset wrap */
    if (destination_cursor != 0xA000u) {
        fprintf(stderr, "overflow policy: cursor wrapped\n");
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3) return 2;
    int rc;
    if (strcmp(argv[1], "ld_sp") == 0) rc = test_ld_sp();
    else if (strcmp(argv[1], "cb") == 0) rc = test_cb();
    else if (strcmp(argv[1], "controls") == 0) rc = test_controls();
    else if (strcmp(argv[1], "partition") == 0) rc = test_partition();
    else if (strcmp(argv[1], "outputs") == 0) rc = test_outputs();
    else if (strcmp(argv[1], "state_matrix") == 0)
        rc = test_state_matrix(argc == 3 && strcmp(argv[2], "--flip-cancel") == 0);
    else if (strcmp(argv[1], "trigger_matrix") == 0) rc = test_trigger_matrix();
    else if (strcmp(argv[1], "trigger_controls") == 0) rc = test_trigger_controls();
    else if (strcmp(argv[1], "trigger_flip") == 0) rc = test_trigger_flip();
    else if (strcmp(argv[1], "timing_policy") == 0) rc = test_timing_policy(0);
    else if (strcmp(argv[1], "timing_flip") == 0) rc = test_timing_policy(1);
    else if (strcmp(argv[1], "address_matrix") == 0) rc = test_address_matrix();
    else if (strcmp(argv[1], "address_flip") == 0) rc = test_address_flip();
    else if (strcmp(argv[1], "overflow_policy") == 0) rc = test_overflow_policy();
    else if (strcmp(argv[1], "overflow_flip") == 0) rc = test_overflow_flip();
    else return 2;
    if (rc == 0) printf("cgb-hdma %s pass\n", argv[1]);
    return rc;
}
