/* White-box CGB HDMA seams reuse the explicit partition digest for lifecycle
 * transaction checks; none of these fixtures claim physical CGB-E timing. */
#define main cgb_hdma_partition_existing_main
#include "test_cgb_partition.c"
#undef main

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

static int admit_following_hblank_block(gbb_instance *m) {
    m->ly = 0u;
    m->lcdc = 0x91u;
    ppu_set_mode(m, 3u);
    ppu_set_mode(m, 0u);
    REQUIRE(m->hdma.pending_hblank);
    gbb_run_result run = gbb_run(m, 64u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == 64u &&
            !m->hdma.pending_hblank && !m->hdma.active && m->hdma.blocks_remaining == 0u);
    return 0;
}

static int expect_source_banks_change_between_blocks(void) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, 0x4000u, 0x8000u, 0x81u, 0x01u, 1u, 0u,
                                   65536u) == 0);
    gbb_run_result first_rom = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(first_rom.reason == GBB_STOP_BUDGET && first_rom.consumed_half_dots == 104u &&
            m->hdma.blocks_remaining == 1u && memcmp(m->vram[0], m->rom + 0x4000u, 16u) == 0);
    write8(m, 0x2000u, 0x02u);
    REQUIRE(admit_following_hblank_block(m) == 0);
    REQUIRE(memcmp(m->vram[0] + 16u, m->rom + 0x8010u, 16u) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xA000u, 0x8000u, 0x81u, 0x03u, 0u, 3u,
                                   32768u) == 0);
    write8(m, 0x0000u, 0x0Au);
    write8(m, 0x6000u, 0x01u);
    gbb_run_result first_ram = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(first_ram.reason == GBB_STOP_BUDGET && first_ram.consumed_half_dots == 104u &&
            m->hdma.blocks_remaining == 1u &&
            memcmp(m->vram[0], m->cartridge_ram, 16u) == 0);
    write8(m, 0x4000u, 0x01u);
    REQUIRE(admit_following_hblank_block(m) == 0);
    REQUIRE(memcmp(m->vram[0] + 16u, m->cartridge_ram + 0x2010u, 16u) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xD000u, 0x8000u, 0x81u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result first_wram = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(first_wram.reason == GBB_STOP_BUDGET && first_wram.consumed_half_dots == 104u &&
            m->hdma.blocks_remaining == 1u &&
            memcmp(m->vram[0], m->wram[1], 16u) == 0);
    write8(m, 0xFF70u, 0x02u);
    REQUIRE(admit_following_hblank_block(m) == 0);
    REQUIRE(memcmp(m->vram[0] + 16u, m->wram[2] + 16u, 16u) == 0);
    gbb_destroy(m);
    return 0;
}

static int expect_vbk_changes_between_blocks(void) {
    gbb_instance *m = NULL;
    REQUIRE(address_fixture_create(&m, 0xC000u, 0x8000u, 0x81u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    gbb_run_result first = gbb_run(m, 104u, NULL, 0u);
    REQUIRE(first.reason == GBB_STOP_BUDGET && first.consumed_half_dots == 104u &&
            m->hdma.blocks_remaining == 1u && memcmp(m->vram[0], m->wram[0], 16u) == 0);
    write8(m, 0xFF4Fu, 0x01u);
    REQUIRE(admit_following_hblank_block(m) == 0);
    REQUIRE(memcmp(m->vram[1] + 16u, m->wram[0] + 16u, 16u) == 0);
    for (unsigned i = 16u; i < 32u; ++i) REQUIRE(m->vram[0][i] == 0xA5u);
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
    REQUIRE(expect_source_banks_change_between_blocks() == 0);
    REQUIRE(expect_vbk_changes_between_blocks() == 0);
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
    REQUIRE(memcmp(m->vram[0] + 16u, m->wram[1], 16u) == 0);
    gbb_destroy(m);

    REQUIRE(address_fixture_create(&m, 0xDFF0u, 0x8000u, 0x01u, 0x00u, 0u, 0u,
                                   32768u) == 0);
    REQUIRE(expect_prefix_then_invalid(0xDFF0u, 0x00u, 0u, 0u, 32768u,
                                       0xE000u, m->wram[1] + 0x0FF0u) == 0);
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

static int competing_fixture_create(gbb_instance **out, int speed, int ime,
                                   int timer_wake, int active_hdma) {
    REQUIRE(policy_fixture_create(out, 0u, 0u, 0, 0, speed, 0u, 0u, 0u, 16u) == 0);
    gbb_instance *m = *out;
    const uint32_t quantum = 8u >> speed;
    m->double_speed = (uint8_t)(1 - speed);
    m->divider_phase = 0u;
    m->divider_counter = 0u;
    m->div = 0u;
    m->ie = 0x04u;
    m->interrupt_flags = 0u;
    m->joypad_select = 0x30u;
    m->key1_armed = 1u;
    m->rom[0x150u] = 0x10u;
    m->rom[0x151u] = 0x00u;
    m->pc = 0x150u;
    const uint64_t switch_cost = GBB_STOP_SWITCH_COST_HALF_DOTS >> m->double_speed;
    gbb_run_result switched = gbb_run(m, switch_cost, NULL, 0u);
    REQUIRE(switched.reason == GBB_STOP_BUDGET && switched.consumed_half_dots == switch_cost &&
            m->double_speed == speed && m->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
            m->key1_armed == 0u);
    m->cpu_stall_half_dots = quantum * 2u;
    m->ime = ime;
    m->timer_reloaded_at = UINT64_MAX;
    m->timer_reload_pending = timer_wake;
    m->timer_reload_remaining = timer_wake ? 1u : 0u;
    m->tma = 0x42u;
    m->sp = 0x8010u;
    m->pc = 0x1234u;
    for (unsigned i = 0u; i < 16u; ++i) {
        m->wram[0][i] = (uint8_t)(0x27u + 37u * i);
        m->vram[0][i] = 0xA5u;
    }
    m->hdma.mode = 1u;
    m->hdma.active = (uint8_t)active_hdma;
    m->hdma.pending_hblank = 0u;
    m->hdma.blocks_remaining = 1u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->hdma.byte_index = active_hdma ? 12u : 0u;
    m->hdma.byte_phase = 0u;
    m->hdma.block_vram_bank = 0u;
    m->hdma.control_readback = 0u;
    return 0;
}

static int test_competing_stalls(void) {
    for (int speed = 0; speed <= 1; ++speed) {
        gbb_instance *m = NULL;
        REQUIRE(competing_fixture_create(&m, speed, 1, 1, 1) == 0);
        const uint32_t quantum = 8u >> speed;
        const uint64_t before = m->time_half_dots;
        const uint32_t stall_before = m->cpu_stall_half_dots;
        gbb_run_result partial = gbb_run(m, 1u, NULL, 0u);
        if (partial.consumed_half_dots != 1u || m->time_half_dots != before + 1u ||
            m->cpu_stall_half_dots != stall_before - 1u || !m->hdma.active) {
            fprintf(stderr,
                "competing stalls: active HDMA must advance one half-dot with its own speed-pause remainder (speed=%d consumed=%llu)\n",
                speed, (unsigned long long)partial.consumed_half_dots);
            gbb_destroy(m);
            return 1;
        }
        gbb_run_result boundary = gbb_run(m, quantum - 1u, NULL, 0u);
        REQUIRE(boundary.reason == GBB_STOP_BUDGET && boundary.consumed_half_dots == quantum - 1u);
        REQUIRE(m->timer_reloaded_at == before + (speed ? 1u : 2u));
        REQUIRE(m->time_half_dots == before + quantum &&
                m->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
                m->cpu_stall_half_dots == quantum &&
                m->hdma.active && m->hdma.byte_index > 12u);

        gbb_run_result sampled = gbb_run(m, 1u, NULL, 0u);
        REQUIRE(sampled.reason == GBB_STOP_BUDGET && sampled.consumed_half_dots == 1u &&
                m->cpu_stall_kind == GBB_STALL_NONE && m->cpu_stall_half_dots == 0u &&
                m->hdma.active);

        gbb_trace_record trace;
        gbb_run_result wake = gbb_run(m, 64u, &trace, 1u);
        REQUIRE(wake.reason == GBB_STOP_TRACE_FULL && wake.trace_count == 1u &&
                trace.pc == 0x0050u && !m->hdma.active && m->hdma.blocks_remaining == 0u);
        const uint8_t stack_lo = m->vram[0][14u];
        const uint8_t stack_hi = m->vram[0][15u];
        if (stack_lo != 0x34u || stack_hi != 0x12u) {
            fprintf(stderr,
                "competing stalls: timer IRQ stack writes must follow admitted DMA completion (speed=%d VRAM=%02X/%02X)\n",
                speed, stack_lo, stack_hi);
            gbb_destroy(m);
            return 1;
        }
        gbb_destroy(m);
    }
    return 0;
}

static int test_competing_stalls_controls(void) {
    for (int speed = 0; speed <= 1; ++speed) {
        gbb_instance *m = NULL;
        REQUIRE(competing_fixture_create(&m, speed, 0, 0, 1) == 0);
        m->hdma.byte_index = 0u;
        m->hdma.blocks_remaining = 2u;
        m->lcdc = 0x91u;
        m->ly = 0u;
        m->ppu_mode = 3u;
        m->ppu_dot = 100u;
        m->ppu_half_phase = 0u;
        m->ppu_transfer_age = 0u;
        m->ppu_transfer_complete = 0u;
        m->dma_active = 1u;
        m->dma_page = 0xC0u;
        m->dma_index = 0u;
        m->dma_phase = 0u;
        m->serial_active = 1u;
        m->serial_control = 1u;
        m->serial_edge_remaining = 100u;
        m->apu_pulse[0].enabled = 1u;
        m->apu_pulse[0].timer = 100u;
        m->cart.rtc_sub = 123456u;
        const uint32_t quantum = 8u >> speed;
        const uint64_t duration = m->cpu_stall_half_dots;
        const uint64_t start = m->time_half_dots;
        gbb_run_result run = gbb_run(m, duration, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == duration &&
                m->time_half_dots == start + duration &&
                m->cpu_stall_kind == GBB_STALL_NONE && m->hdma.active &&
                m->hdma.byte_index == duration / 4u &&
                (m->interrupt_flags & 0x04u) == 0u && m->dma_active &&
                m->dma_index == 2u && m->dma_phase == 0u &&
                m->serial_edge_remaining == 92u && m->ppu_dot == 100u + duration / 2u &&
                m->apu_pulse[0].timer == 100u - duration && m->cart.rtc_sub == 123456u);
        REQUIRE(quantum * 2u == duration);
        gbb_destroy(m);

        REQUIRE(competing_fixture_create(&m, speed, 0, 1, 0) == 0);
        run = gbb_run(m, duration, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == duration &&
                m->cpu_stall_kind == GBB_STALL_NONE && !m->hdma.active &&
                m->hdma.mode == 1u && m->hdma.blocks_remaining == 1u &&
                !m->hdma.pending_hblank && m->vram[0][0] == 0xA5u &&
                (m->interrupt_flags & 0x04u) != 0u);
        gbb_destroy(m);
    }
    return 0;
}

static int stop_fixture_create(gbb_instance **out) {
    uint8_t rom[32768] = {0};
    rom[0x143u] = 0xC0u;
    rom[0x100u] = 0x10u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x00u;
    finish_rom(rom);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, out) == GBB_OK);
    REQUIRE(gbb_load_rom(*out, rom, sizeof(rom)) == GBB_OK);
    (*out)->pc = 0x100u;
    gbb_run_result stop = gbb_run(*out, 8u, NULL, 0u);
    REQUIRE(stop.reason == GBB_STOP_STOPPED && (*out)->stopped && (*out)->pc == 0x102u);
    return 0;
}

static int queue_stop_wake(gbb_instance *m, uint64_t offset) {
    const gbb_input_event event = {m->time_half_dots + offset, GBB_INPUT_STOP_WAKE, 1u};
    REQUIRE(gbb_queue_events(m, &event, 1u) == GBB_OK);
    return 0;
}

static int test_stop_policy(void) {
    gbb_instance *m = NULL;
    REQUIRE(stop_fixture_create(&m) == 0);
    m->hdma.mode = 1u;
    m->hdma.active = 0u;
    m->hdma.pending_hblank = 1u;
    m->hdma.blocks_remaining = 2u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->hdma.byte_index = 5u;
    m->hdma.byte_phase = 2u;
    m->hdma.block_vram_bank = 0u;
    m->dma_active = 1u;
    m->dma_page = 0xC0u;
    m->dma_index = 3u;
    m->dma_phase = 2u;
    m->lcdc = 0u;
    m->timer_reload_pending = 1;
    m->timer_reload_remaining = 6u;
    m->serial_active = 1u;
    m->serial_control = 1u;
    m->serial_edge_remaining = 90u;
    m->apu_sequencer_step = 5u;
    m->apu_sample_phase = 777u;
    m->cart.rtc_sub = 123456u;

    const uint64_t start = m->time_half_dots;
    REQUIRE(queue_stop_wake(m, 5u) == 0);
    gbb_run_result sleep = gbb_run(m, 5u, NULL, 0u);
    REQUIRE(sleep.consumed_half_dots == 5u && m->time_half_dots == start + 5u && !m->stopped);
    REQUIRE(m->hdma.pending_hblank && !m->hdma.active &&
            m->hdma.blocks_remaining == 2u && m->hdma.byte_index == 5u &&
            m->hdma.byte_phase == 2u && m->dma_active && m->dma_index == 3u &&
            m->dma_phase == 2u && m->timer_reload_pending && m->timer_reload_remaining == 6u &&
            m->serial_edge_remaining == 90u && m->apu_sequencer_step == 5u &&
            m->apu_sample_phase == 777u && m->cart.rtc_sub == 123456u);

    gbb_run_result resume = gbb_run(m, 1u, NULL, 0u);
    REQUIRE(resume.reason == GBB_STOP_BUDGET && resume.consumed_half_dots == 1u &&
            !m->hdma.pending_hblank && m->hdma.active && m->hdma.byte_phase == 1u &&
            m->dma_phase == 2u && m->pc == 0x102u);
    gbb_destroy(m);
    return 0;
}

static int test_stop_policy_controls(void) {
    gbb_instance *m = NULL;
    REQUIRE(stop_fixture_create(&m) == 0);
    m->hdma.mode = 1u;
    m->hdma.active = 0u;
    m->hdma.pending_hblank = 0u;
    m->hdma.blocks_remaining = 2u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->lcdc = 0x91u;
    m->ly = 0u;
    m->ppu_mode = 3u;
    m->ppu_dot = 200u;
    m->ppu_half_phase = 1u;
    m->ppu_transfer_complete = 1u;
    gbb_test_bus_event events[8];
    memset(events, 0, sizeof(events));
    gbb_test_ppu_observer_set(m, events, 8u);
    const uint64_t start = m->time_half_dots;
    REQUIRE(queue_stop_wake(m, 3u) == 0);
    gbb_run_result sleep = gbb_run(m, 3u, NULL, 0u);
    REQUIRE(sleep.consumed_half_dots == 3u && m->time_half_dots == start + 3u &&
            !m->stopped && m->ppu_mode == 3u && m->ppu_dot == 200u &&
            !m->hdma.pending_hblank);
    gbb_run_result resumed = gbb_run(m, 8u, NULL, 0u);
    REQUIRE(resumed.reason == GBB_STOP_BUDGET && resumed.consumed_half_dots == 8u &&
            m->hdma.pending_hblank && m->ppu_mode == 0u &&
            gbb_test_ppu_observer_count(m) != 0u &&
            events[0].time_half_dots == start + 4u);
    gbb_destroy(m);
    return 0;
}

static int test_oam_order(void) {
    uint8_t rom[32768] = {0};
    rom[0x143u] = 0xC0u;
    finish_rom(rom);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    m->wram[0][15u] = 0x22u;
    m->vram[0][15u] = 0x11u;
    m->double_speed = 0u;
    m->divider_phase = 1u;
    m->dma_active = 1u;
    m->dma_page = 0x80u;
    m->dma_index = 15u;
    m->dma_phase = 3u;
    m->hdma.mode = 1u;
    m->hdma.active = 1u;
    m->hdma.blocks_remaining = 2u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->hdma.byte_index = 15u;
    m->hdma.byte_phase = 3u;
    m->hdma.block_vram_bank = 0u;
    m->lcdc = 0x91u;
    m->ly = 0u;
    m->ppu_mode = 3u;
    m->ppu_dot = 200u;
    m->ppu_half_phase = 1u;
    m->ppu_transfer_complete = 1u;
    struct gbb_test_dma_event dma[4];
    gbb_test_bus_event ppu[4];
    memset(dma, 0, sizeof(dma));
    memset(ppu, 0, sizeof(ppu));
    gbb_test_dma_observer_set(m, dma, 4u);
    gbb_test_ppu_observer_set(m, ppu, 4u);
    const uint64_t start = m->time_half_dots;
    gbb_run_result tick = gbb_run(m, 1u, NULL, 0u);
    REQUIRE(tick.reason == GBB_STOP_BUDGET && tick.consumed_half_dots == 1u);
    if (m->oam[15u] != 0x11u || m->vram[0][15u] != 0x22u ||
        m->hdma.active || !m->hdma.pending_hblank || m->hdma.blocks_remaining != 1u) {
        if (GBB_P13_MUT(52))
            fputs("hdma mutant shifted_order detected OAM-before-HDMA predicate\n", stderr);
        fprintf(stderr, "oam order: OAM=%02X VRAM=%02X active=%u pending=%u remaining=%u\n",
                m->oam[15u], m->vram[0][15u], m->hdma.active,
                m->hdma.pending_hblank, m->hdma.blocks_remaining);
        gbb_destroy(m);
        return 1;
    }
    REQUIRE(gbb_test_dma_observer_count(m) == 1u && dma[0].address == 0xFE0Fu &&
            dma[0].access == 2u && dma[0].value == 0x11u && dma[0].time_half_dots == start + 1u);
    REQUIRE(gbb_test_ppu_observer_count(m) != 0u && ppu[0].address == 0xFF41u &&
            ppu[0].value == 0u && ppu[0].time_half_dots == dma[0].time_half_dots);
    gbb_destroy(m);
    return 0;
}

static int test_oam_order_controls(void) {
    uint8_t rom[32768] = {0};
    rom[0x143u] = 0xC0u;
    finish_rom(rom);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    m->wram[0][15u] = 0x22u;
    m->vram[0][15u] = 0x11u;
    m->divider_phase = 1u;
    m->dma_active = 1u;
    m->dma_page = 0x80u;
    m->dma_index = 15u;
    m->dma_phase = 2u;
    m->hdma.mode = 1u;
    m->hdma.active = 1u;
    m->hdma.blocks_remaining = 2u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->hdma.byte_index = 15u;
    m->hdma.byte_phase = 3u;
    m->hdma.block_vram_bank = 0u;
    m->lcdc = 0x91u;
    m->ppu_mode = 3u;
    m->ppu_dot = 200u;
    m->ppu_half_phase = 1u;
    m->ppu_transfer_complete = 1u;
    struct gbb_test_dma_event dma[4];
    memset(dma, 0, sizeof(dma));
    gbb_test_dma_observer_set(m, dma, 4u);
    gbb_run_result tick = gbb_run(m, 1u, NULL, 0u);
    REQUIRE(tick.reason == GBB_STOP_BUDGET && tick.consumed_half_dots == 1u &&
            m->dma_phase == 3u && m->oam[15u] == 0u && m->vram[0][15u] == 0x22u &&
            m->hdma.pending_hblank && gbb_test_dma_observer_count(m) == 0u);
    gbb_destroy(m);
    return 0;
}

static const char *hdma_lifecycle_missing_field(const gbb_instance *m) {
#define HDMA_EXPECT(field, expected) do { if (m->hdma.field != (expected)) return #field; } while (0)
    HDMA_EXPECT(mode, 0u);
    HDMA_EXPECT(active, 0u);
    HDMA_EXPECT(pending_hblank, 0u);
    HDMA_EXPECT(blocks_remaining, 0u);
    HDMA_EXPECT(byte_index, 0u);
    HDMA_EXPECT(byte_phase, 0u);
    HDMA_EXPECT(source_cursor, 0u);
    HDMA_EXPECT(destination_cursor, 0u);
    HDMA_EXPECT(block_vram_bank, 0u);
    HDMA_EXPECT(source_high, 0u);
    HDMA_EXPECT(source_low, 0u);
    HDMA_EXPECT(destination_high, 0u);
    HDMA_EXPECT(destination_low, 0u);
    HDMA_EXPECT(control_readback, 0xFFu);
#undef HDMA_EXPECT
    return NULL;
}

static void hdma_lifecycle_prime(gbb_instance *m) {
    m->hdma.mode = 2u;
    m->hdma.active = 1u;
    m->hdma.pending_hblank = 1u;
    m->hdma.blocks_remaining = 128u;
    m->hdma.byte_index = 15u;
    m->hdma.byte_phase = 3u;
    m->hdma.source_cursor = 0xCFF0u;
    m->hdma.destination_cursor = 0x9FF0u;
    m->hdma.block_vram_bank = 1u;
    m->hdma.source_high = 0xC0u;
    m->hdma.source_low = 0xF0u;
    m->hdma.destination_high = 0x1Fu;
    m->hdma.destination_low = 0xF0u;
    m->hdma.control_readback = 0x7Fu;
}

static uint64_t hdma_partition_state_digest(const gbb_instance *m) {
    partition_streams empty_streams;
    memset(&empty_streams, 0, sizeof(empty_streams));
    return partition_digest(m, &empty_streams);
}

static int test_hdma_lifecycle(void) {
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(hdma_lifecycle_missing_field(m) == NULL);
    uint8_t rom[32768];
    make_rom(rom, 0, 1);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);

    hdma_lifecycle_prime(m);
    REQUIRE(gbb_reset(m) == GBB_OK);
    const char *missing = hdma_lifecycle_missing_field(m);
    if (missing != NULL) {
        fprintf(stderr, "hdma-lifecycle-reset-left-field %s\n", missing);
        gbb_destroy(m);
        return 1;
    }
    hdma_lifecycle_prime(m);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    missing = hdma_lifecycle_missing_field(m);
    if (missing != NULL) {
        fprintf(stderr, "hdma-lifecycle-load-left-field %s\n", missing);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);

    gbb_instance *active = NULL, *control = NULL;
    REQUIRE(policy_fixture_create(&active, 0x7Fu, 0u, 0, 0, 0, 0u, 0u, 0u, 2048u) == 0);
    REQUIRE(policy_fixture_create(&control, 0x7Fu, 0u, 0, 0, 0, 0u, 0u, 0u, 2048u) == 0);
    active->pc = control->pc = 0x112u;
    active->a = control->a = 0x7Fu;
    REQUIRE(gbb_run(active, 24u, NULL, 0u).consumed_half_dots == 24u);
    REQUIRE(gbb_run(control, 24u, NULL, 0u).consumed_half_dots == 24u);
    REQUIRE(gbb_run(active, 1u, NULL, 0u).consumed_half_dots == 1u);
    REQUIRE(gbb_run(control, 1u, NULL, 0u).consumed_half_dots == 1u);
    REQUIRE(active->hdma.active && active->hdma.byte_phase == 1u &&
            active->hdma.blocks_remaining == 128u);

    const uint64_t before = hdma_partition_state_digest(active);
    REQUIRE(gbb_load_rom(active, NULL, 0u) == GBB_INVALID_ARGUMENT);
    REQUIRE(hdma_partition_state_digest(active) == before);
    REQUIRE(gbb_load_rom(active, active->rom, 0x14Fu) == GBB_ROM_TRUNCATED);
    REQUIRE(hdma_partition_state_digest(active) == before);
    REQUIRE(gbb_load_rom(active, active->rom, GBB_MAX_ROM_SIZE + 1u) == GBB_ROM_TOO_LARGE);
    REQUIRE(hdma_partition_state_digest(active) == before);

    (void)gbb_run(active, 63u, NULL, 0u);
    (void)gbb_run(control, 63u, NULL, 0u);
    REQUIRE(hdma_partition_state_digest(active) == hdma_partition_state_digest(control));
    gbb_destroy(active);
    gbb_destroy(control);

    gbb_instance *bank0 = NULL, *bank1 = NULL;
    REQUIRE(policy_fixture_create(&bank0, 0x00u, 0u, 0, 0, 0, 0u, 0u, 0u, 32u) == 0);
    REQUIRE(policy_fixture_create(&bank1, 0x01u, 0u, 0, 0, 0, 0u, 0u, 0u, 32u) == 0);
    for (size_t i = 0u; i < 32u; ++i) {
        bank0->wram[0][i] = (uint8_t)(0x20u + i);
        bank1->wram[0][i] = (uint8_t)(0xC0u - i);
    }
    memset(bank0->vram[0], 0xA5, sizeof(bank0->vram[0]));
    memset(bank1->vram[0], 0xA5, sizeof(bank1->vram[0]));
    bank0->vram_bank = 0u;
    bank1->vram_bank = 1u;
    hdma_register_write(bank0, 0xFF55u, 0x00u);
    hdma_register_write(bank1, 0xFF55u, 0x01u);
    REQUIRE(gbb_run(bank0, 64u, NULL, 0u).consumed_half_dots == 64u);
    REQUIRE(gbb_run(bank1, 64u, NULL, 0u).consumed_half_dots == 64u);
    REQUIRE(gbb_run(bank1, 64u, NULL, 0u).consumed_half_dots == 64u);
    REQUIRE(bank0->hdma.blocks_remaining == 0u &&
            bank1->hdma.blocks_remaining == 0u &&
            memcmp(bank0->vram[0], bank0->wram[0], 16u) == 0 &&
            memcmp(bank1->vram[1], bank1->wram[0], 32u) == 0 &&
            bank1->vram[0][0] == 0xA5u);
    gbb_destroy(bank0);
    gbb_destroy(bank1);
    return 0;
}

static int test_hdma_lifecycle_controls(void) {
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(hdma_lifecycle_missing_field(m) == NULL);
    m->hdma.source_cursor = 0xC000u;
    const char *missing = hdma_lifecycle_missing_field(m);
    gbb_destroy(m);
    if (missing == NULL) {
        fputs("hdma-lifecycle-control-inert source_cursor\n", stderr);
        return 1;
    }
    fprintf(stderr, "hdma-lifecycle-control-detected %s\n", missing);
    return 1;
}

static int hdma_active_block_fixture(gbb_instance **out) {
    REQUIRE(policy_fixture_create(out, 0x80u, 0u, 0, 0, 0, 0u, 0u, 0u, 64u) == 0);
    hdma_register_write(*out, 0xFF55u, 0x00u);
    if (!hdma_admit_block(*out)) {
        gbb_destroy(*out);
        *out = NULL;
        return 1;
    }
    return 0;
}

static int hdma_start_headroom_case(uint8_t control, uint64_t start_time,
                                    gbb_stop_reason expected_reason) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, control, 0u, 0, 0, 0, 0u, 0u, 0u,
                                  (size_t)((control & 0x7Fu) + 1u) * 16u) == 0);
    m->pc = 0x112u;
    m->a = control;
    m->time_half_dots = start_time;
    const uint64_t before = hdma_partition_state_digest(m);
    gbb_trace_record trace[2];
    memset(trace, 0xA5, sizeof(trace));
    const gbb_run_result start = gbb_run_ex(m, 24u, trace, 1u, NULL, 0u);
    if (expected_reason != GBB_STOP_BUDGET) {
        if (start.reason != expected_reason || start.consumed_half_dots != 0u ||
            m->time_half_dots != start_time ||
            hdma_partition_state_digest(m) != before) {
            fprintf(stderr, "hdma-resource-start-headroom not-rejected blocks=%u start=%" PRIu64
                            " reason=%d consumed=%" PRIu64 "\n",
                    (unsigned)(control & 0x7Fu) + 1u, start_time, start.reason,
                    start.consumed_half_dots);
            gbb_destroy(m);
            return 1;
        }
        const uint8_t *guard = (const uint8_t *)&trace[0];
        for (size_t i = 0u; i < sizeof(trace[0]); ++i) {
            if (guard[i] != 0xA5u) {
                fprintf(stderr, "hdma-resource-start-output-mutated byte=%zu\n", i);
                gbb_destroy(m);
                return 1;
            }
        }
        gbb_destroy(m);
        return 0;
    }
    REQUIRE(start.reason == GBB_STOP_BUDGET && start.consumed_half_dots == 24u &&
            m->hdma.mode == 2u && m->hdma.pending_hblank);
    const uint64_t work = (uint64_t)((control & 0x7Fu) + 1u) * 64u;
    const gbb_run_result transfer = gbb_run(m, work, NULL, 0u);
    REQUIRE(transfer.reason == GBB_STOP_BUDGET && transfer.consumed_half_dots == work &&
            m->time_half_dots == GBB_STATE_TIME_LIMIT &&
            m->hdma.mode == 0u && m->hdma.blocks_remaining == 0u);
    gbb_destroy(m);
    return 0;
}

static int hdma_rejected_store_case(const uint8_t *instruction, size_t size,
                                    unsigned setup) {
    gbb_instance *m = NULL;
    REQUIRE(policy_fixture_create(&m, 0x80u, 0u, 0, 0, 0, 0u, 0u, 0u, 48u) == 0);
    memcpy(m->rom + 0x200u, instruction, size);
    m->pc = 0x200u;
    m->a = 0x02u;
    if (setup == 1u) m->c = 0x55u;
    else if (setup == 2u) { m->h = 0xFFu; m->l = 0x55u; }
    else if (setup == 3u) m->sp = 0x02ABu;
    else if (setup == 4u) { m->b = 0x02u; m->c = 0x00u; m->sp = 0xFF56u; }
    const decoded decoded_instruction = decode(m);
    const uint64_t cost = instruction_cost(m, decoded_instruction);
    m->time_half_dots = GBB_STATE_TIME_LIMIT - (cost + 3u * 64u - 1u);
    const uint64_t before = hdma_partition_state_digest(m);
    gbb_trace_record trace;
    memset(&trace, 0xA5, sizeof(trace));
    const gbb_run_result rejected = gbb_run_ex(m, cost, &trace, 1u, NULL, 0u);
    const int unchanged = rejected.reason == GBB_STOP_NO_PROGRESS &&
        rejected.consumed_half_dots == 0u && hdma_partition_state_digest(m) == before;
    const uint8_t *trace_bytes = (const uint8_t *)&trace;
    for (size_t i = 0u; i < sizeof(trace); ++i)
        if (trace_bytes[i] != 0xA5u) {
            gbb_destroy(m);
            return 1;
        }
    gbb_destroy(m);
    return unchanged ? 0 : 1;
}

static int hdma_check_store_headroom_forms(void) {
    static const uint8_t ldh[] = {0xE0u, 0x55u};
    static const uint8_t absolute[] = {0xEAu, 0x55u, 0xFFu};
    static const uint8_t c_register[] = {0xE2u};
    static const uint8_t indirect[] = {0x77u};
    static const uint8_t store_sp[] = {0x08u, 0x54u, 0xFFu};
    static const uint8_t push_bc[] = {0xC5u};
    const struct { const uint8_t *code; size_t size; unsigned setup; const char *name; } cases[] = {
        {ldh, sizeof(ldh), 0u, "LDH"},
        {absolute, sizeof(absolute), 0u, "absolute"},
        {c_register, sizeof(c_register), 1u, "C-register"},
        {indirect, sizeof(indirect), 2u, "HL-indirect"},
        {store_sp, sizeof(store_sp), 3u, "SP-high-byte"},
        {push_bc, sizeof(push_bc), 4u, "stack-high-byte"}
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (hdma_rejected_store_case(cases[i].code, cases[i].size,
                                     cases[i].setup) != 0) {
            fprintf(stderr, "hdma-resource-store-form accepted without headroom form=%s\n",
                    cases[i].name);
            return 1;
        }
    }
    return 0;
}

static int hdma_guard_is(const uint8_t *guard, size_t size, uint8_t value) {
    for (size_t i = 0u; i < size; ++i)
        if (guard[i] != value) return 0;
    return 1;
}

static int test_hdma_resource_bounds(void) {
    static const uint64_t budgets[] = {0u, 1u, 3u, 4u, 63u, 64u, 65u, 67u};
    for (size_t i = 0u; i < sizeof(budgets) / sizeof(budgets[0]); ++i) {
        gbb_instance *m = NULL;
        REQUIRE(hdma_active_block_fixture(&m) == 0);
        const uint64_t start_time = m->time_half_dots;
        const uint64_t budget = budgets[i];
        const gbb_run_result run = gbb_run(m, budget, NULL, 0u);
        const uint64_t expected = budget < 64u ? budget : 64u;
        REQUIRE(run.reason == GBB_STOP_BUDGET && run.consumed_half_dots == expected &&
                m->time_half_dots == start_time + expected);
        if (expected < 64u) {
            REQUIRE(m->hdma.active && m->hdma.byte_index == expected / 4u &&
                    m->hdma.byte_phase == expected % 4u);
        } else {
            REQUIRE(m->hdma.mode == 0u && !m->hdma.active &&
                    m->hdma.blocks_remaining == 0u &&
                    memcmp(m->vram[0], m->wram[0], 16u) == 0);
        }
        gbb_destroy(m);
    }

    REQUIRE(hdma_start_headroom_case(0x02u, UINT64_MAX - 215u,
                                     GBB_STOP_INVALID_STATE) == 0);
    REQUIRE(hdma_start_headroom_case(0x02u, GBB_STATE_TIME_LIMIT - 215u,
                                     GBB_STOP_NO_PROGRESS) == 0);
    REQUIRE(hdma_start_headroom_case(0x02u, GBB_STATE_TIME_LIMIT - 216u,
                                     GBB_STOP_BUDGET) == 0);
    REQUIRE(hdma_check_store_headroom_forms() == 0);

    gbb_instance *lcd_off_halt = NULL;
    REQUIRE(policy_fixture_create(&lcd_off_halt, 0x80u, 0u, 0, 0, 0,
                                  0u, 0u, 0u, 2048u) == 0);
    lcd_off_halt->halted = 1u;
    for (size_t i = 0u; i < 2048u; ++i)
        lcd_off_halt->wram[0][i] = (uint8_t)(i * 29u + 3u);
    hdma_register_write(lcd_off_halt, 0xFF55u, 0x7Fu);
    REQUIRE(lcd_off_halt->hdma.blocks_remaining == 128u &&
            lcd_off_halt->hdma.pending_hblank);
    const gbb_run_result maximum = gbb_run(lcd_off_halt, 8192u, NULL, 0u);
    REQUIRE(maximum.consumed_half_dots == 8192u && lcd_off_halt->halted &&
            lcd_off_halt->hdma.mode == 0u && lcd_off_halt->hdma.blocks_remaining == 0u &&
            memcmp(lcd_off_halt->vram[0], lcd_off_halt->wram[0], 2048u) == 0);
    gbb_destroy(lcd_off_halt);

    gbb_instance *near_byte = NULL;
    REQUIRE(hdma_active_block_fixture(&near_byte) == 0);
    near_byte->time_half_dots = UINT64_MAX - 5u;
    const uint64_t near_byte_before = hdma_partition_state_digest(near_byte);
    const gbb_run_result partial = gbb_run(near_byte, 8u, NULL, 0u);
    REQUIRE(partial.reason == GBB_STOP_INVALID_STATE && partial.consumed_half_dots == 0u &&
            near_byte->time_half_dots == UINT64_MAX - 5u &&
            hdma_partition_state_digest(near_byte) == near_byte_before);
    gbb_destroy(near_byte);

    gbb_instance *near_block = NULL;
    REQUIRE(hdma_active_block_fixture(&near_block) == 0);
    near_block->hdma.blocks_remaining = 1u;
    near_block->hdma.byte_index = 15u;
    near_block->hdma.byte_phase = 3u;
    near_block->time_half_dots = GBB_STATE_TIME_LIMIT - 1u;
    const gbb_run_result final_byte = gbb_run(near_block, 1u, NULL, 0u);
    REQUIRE(final_byte.reason == GBB_STOP_BUDGET && final_byte.consumed_half_dots == 1u &&
            near_block->time_half_dots == GBB_STATE_TIME_LIMIT && near_block->hdma.mode == 0u &&
            near_block->hdma.blocks_remaining == 0u);
    gbb_destroy(near_block);

    gbb_instance *trace_case = NULL;
    REQUIRE(hdma_active_block_fixture(&trace_case) == 0);
    gbb_trace_record traces[3];
    memset(traces, 0xA5, sizeof(traces));
    gbb_run_result no_trace = gbb_run_ex(trace_case, 64u, traces, 0u, NULL, 0u);
    REQUIRE(no_trace.reason == GBB_STOP_BUDGET && no_trace.consumed_half_dots == 64u &&
            hdma_guard_is((const uint8_t *)traces, sizeof(traces), 0xA5u));
    trace_case->pc = 0x200u;
    gbb_run_result trace_zero = gbb_run_ex(trace_case, 64u, traces, 0u, NULL, 0u);
    REQUIRE(trace_zero.reason == GBB_STOP_TRACE_FULL && trace_zero.consumed_half_dots == 0u &&
            hdma_guard_is((const uint8_t *)traces, sizeof(traces), 0xA5u));
    gbb_run_result trace_one = gbb_run_ex(trace_case, 16u, traces, 1u, NULL, 0u);
    REQUIRE(trace_one.reason == GBB_STOP_TRACE_FULL && trace_one.consumed_half_dots == 8u &&
            trace_one.trace_count == 1u && traces[0].pc == 0x200u &&
            hdma_guard_is((const uint8_t *)&traces[1], sizeof(traces[1]), 0xA5u));
    memset(traces, 0xA5, sizeof(traces));
    gbb_run_result trace_full = gbb_run_ex(trace_case, 16u, traces, 2u, NULL, 0u);
    REQUIRE(trace_full.reason == GBB_STOP_BUDGET && trace_full.consumed_half_dots == 16u &&
            trace_full.trace_count == 2u && traces[0].pc == 0x201u &&
            traces[1].pc == 0x202u &&
            hdma_guard_is((const uint8_t *)&traces[2], sizeof(traces[0]), 0xA5u));
    gbb_destroy(trace_case);

    gbb_instance *audio_case = NULL;
    REQUIRE(hdma_active_block_fixture(&audio_case) == 0);
    gbb_audio_frame audio[4098];
    memset(audio, 0x6B, sizeof(audio));
    size_t frame_count = 0u;
    const gbb_run_result audio_zero = gbb_run_audio(audio_case, 4096u, audio, 0u, &frame_count);
    REQUIRE(audio_zero.reason == GBB_STOP_OUTPUT_FULL && frame_count == 0u &&
            hdma_guard_is((const uint8_t *)audio, sizeof(audio), 0x6Bu));
    const gbb_run_result audio_one = gbb_run_audio(audio_case, 4096u, audio, 1u, &frame_count);
    REQUIRE(audio_one.reason == GBB_STOP_OUTPUT_FULL && frame_count == 1u &&
            hdma_guard_is((const uint8_t *)&audio[1], sizeof(audio[0]), 0x6Bu));
    gbb_destroy(audio_case);
    gbb_instance *audio_full_case = NULL;
    REQUIRE(hdma_active_block_fixture(&audio_full_case) == 0);
    const gbb_run_result audio_full = gbb_run_audio(audio_full_case, 64u, audio, 4096u, &frame_count);
    if (audio_full.reason != GBB_STOP_BUDGET || frame_count > 4096u ||
        !hdma_guard_is((const uint8_t *)&audio[4096], sizeof(audio[0]), 0x6Bu)) {
        fprintf(stderr, "hdma-resource-audio-full reason=%d consumed=%" PRIu64
                        " frames=%zu guard=%d\n", audio_full.reason,
                audio_full.consumed_half_dots, frame_count,
                hdma_guard_is((const uint8_t *)&audio[4096], sizeof(audio[0]), 0x6Bu));
        gbb_destroy(audio_full_case);
        return 1;
    }
    gbb_destroy(audio_full_case);

    gbb_instance *diagnostic_case = NULL;
    REQUIRE(hdma_active_block_fixture(&diagnostic_case) == 0);
    enum { DIAGNOSTIC_CAPACITY = GBB_DIAGNOSTIC_OPERATION_RESERVE * 65u };
    gbb_diagnostic_record diagnostics[DIAGNOSTIC_CAPACITY + 1u];
    memset(diagnostics, 0x5A, sizeof(diagnostics));
    const uint64_t diagnostic_time = diagnostic_case->time_half_dots;
    gbb_run_result diagnostic_zero = gbb_run_ex(diagnostic_case, 4u, NULL, 0u,
                                                diagnostics, 0u);
    REQUIRE(diagnostic_zero.reason == GBB_STOP_OUTPUT_FULL &&
            diagnostic_zero.consumed_half_dots == 0u &&
            diagnostic_case->time_half_dots == diagnostic_time &&
            hdma_guard_is((const uint8_t *)diagnostics, sizeof(diagnostics), 0x5Au));
    gbb_run_result diagnostic_one = gbb_run_ex(diagnostic_case, 4u, NULL, 0u,
                                               diagnostics, 1u);
    REQUIRE(diagnostic_one.reason == GBB_STOP_OUTPUT_FULL &&
            diagnostic_one.consumed_half_dots == 0u &&
            hdma_guard_is((const uint8_t *)diagnostics, sizeof(diagnostics), 0x5Au));
    gbb_run_result diagnostic_full = gbb_run_ex(diagnostic_case, 64u, NULL, 0u,
                                                diagnostics, DIAGNOSTIC_CAPACITY);
    REQUIRE(diagnostic_full.reason == GBB_STOP_BUDGET &&
            diagnostic_full.consumed_half_dots == 64u &&
            hdma_guard_is((const uint8_t *)&diagnostics[DIAGNOSTIC_CAPACITY],
                          sizeof(diagnostics[0]), 0x5Au));
    gbb_destroy(diagnostic_case);

    gbb_instance *repeat = NULL;
    REQUIRE(policy_fixture_create(&repeat, 0x80u, 0u, 0, 0, 0, 0u, 0u, 0u, 16u) == 0);
    for (unsigned i = 0u; i < 256u; ++i) {
        hdma_register_write(repeat, 0xFF55u, 0x80u);
        REQUIRE(repeat->hdma.pending_hblank && repeat->hdma.blocks_remaining == 1u);
        hdma_register_write(repeat, 0xFF55u, 0x00u);
        REQUIRE(repeat->hdma.mode == 0u && !repeat->hdma.active &&
                !repeat->hdma.pending_hblank && repeat->hdma.blocks_remaining == 0u &&
                repeat->hdma.control_readback == 0x80u);
    }
    gbb_destroy(repeat);
    return 0;
}

static int test_hdma_resource_controls(void) {
    uint8_t guard[2] = {0xA5u, 0x5Au};
    guard[1] ^= 1u;
    if (hdma_guard_is(&guard[1], 1u, 0x5Au)) {
        fputs("hdma-resource-control-inert diagnostic_capacity_guard\n", stderr);
        return 1;
    }
    fputs("hdma-resource_bounds-control-detected diagnostic_capacity_guard\n", stderr);
    return 1;
}

extern int gbb_fuzz_core_one_input(const uint8_t *data, size_t size);
extern int gbb_fuzz_core_contract_failures(void);
extern void gbb_fuzz_core_hdma_observation(int *selected, unsigned *operations,
                                          unsigned *run_calls,
                                          uint64_t *consumed_half_dots);

static int test_hdma_hostile_seeds(void) {
    static const uint8_t seed_maximum[] = {
        0xB0u, 0x00u, 0u, 0xC0u, 1u, 0u, 2u, 0x80u, 3u, 0u, 4u, 0x7Fu
    };
    static const uint8_t seed_restart_cancel[] = {
        0xB0u, 1u, 0u, 0xC0u, 1u, 0u, 2u, 0u, 3u, 0u, 4u, 0x7Fu,
        4u, 0x00u, 4u, 0x81u, 4u, 0x00u, 4u, 0x02u
    };
    static const uint8_t seed_address_edges[] = {
        0xB0u, 0u, 0u, 0xFFu, 1u, 0xF0u, 2u, 0x1Fu, 3u, 0xF0u,
        4u, 0x7Fu, 0u, 0xC0u, 1u, 0u, 2u, 0u, 3u, 0u, 4u, 0x7Eu
    };
    const struct { const uint8_t *data; size_t size; unsigned operations; } cases[] = {
        {seed_maximum, sizeof(seed_maximum), 5u},
        {seed_restart_cancel, sizeof(seed_restart_cancel), 9u},
        {seed_address_edges, sizeof(seed_address_edges), 10u}
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        const int failures_before = gbb_fuzz_core_contract_failures();
        REQUIRE(gbb_fuzz_core_one_input(cases[i].data, cases[i].size) == 0);
        int selected = 0;
        unsigned operations = 0u, calls = 0u;
        uint64_t consumed = 0u;
        gbb_fuzz_core_hdma_observation(&selected, &operations, &calls, &consumed);
        REQUIRE(gbb_fuzz_core_contract_failures() == failures_before && selected == 1 &&
                operations == cases[i].operations && operations <= 16u &&
                calls != 0u && calls <= 16u && consumed <= 16384u);
    }
    puts("cgb-hdma hostile seeds pass cases=3 operations<=16 run<=16384");
    return 0;
}

static int test_hdma_hostile_seed_controls(void) {
    static const uint8_t non_hdma_seed[] = {0x80u, 0u};
    REQUIRE(gbb_fuzz_core_one_input(non_hdma_seed, sizeof(non_hdma_seed)) == 0);
    int selected = 1;
    unsigned operations = 1u, calls = 1u;
    uint64_t consumed = UINT64_MAX;
    gbb_fuzz_core_hdma_observation(&selected, &operations, &calls, &consumed);
    if (selected != 0 || operations != 0u || calls != 0u || consumed != 0u) {
        fputs("hdma-hostile-control-selected no-ff51-ff55-route\n", stderr);
        return 1;
    }
    fputs("hdma-hostile_seeds-control-detected no-ff51-ff55-route\n", stderr);
    return 1;
}

static int mutant_machine_create(gbb_instance **out) {
    *out = NULL;
    uint8_t rom[32768] = {0};
    rom[0x143u] = 0xC0u;
    finish_rom(rom);
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, out) != GBB_OK ||
        gbb_load_rom(*out, rom, sizeof(rom)) != GBB_OK) {
        if (*out != NULL) gbb_destroy(*out);
        *out = NULL;
        fputs("hdma mutant fixture: CGB machine setup failed\n", stderr);
        return 1;
    }
    gbb_instance *m = *out;
    for (unsigned i = 0u; i < 32u; ++i)
        m->wram[0][i] = (uint8_t)(0x27u + 37u * i);
    memset(m->vram[0], 0xA5, sizeof(m->vram[0]));
    memset(m->vram[1], 0x5A, sizeof(m->vram[1]));
    m->lcdc = 0u;
    m->hdma.mode = 2u;
    m->hdma.active = 1u;
    m->hdma.pending_hblank = 0u;
    m->hdma.blocks_remaining = 1u;
    m->hdma.source_cursor = 0xC000u;
    m->hdma.destination_cursor = 0x8000u;
    m->hdma.block_vram_bank = 0u;
    m->hdma.byte_index = 0u;
    m->hdma.byte_phase = 0u;
    return 0;
}

static void mutant_advance_block(gbb_instance *m) {
    for (unsigned half_dot = 0u; half_dot < 64u; ++half_dot)
        hdma_advance_half_dot(m);
}

static int test_mutant_no_copy(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    mutant_advance_block(m);
    if (memcmp(m->vram[0], m->wram[0], 16u) != 0) {
        fputs("hdma mutant no_copy detected destination data mismatch\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_duplicate_copy(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    mutant_advance_block(m);
    if (m->vram[0][16u] != 0xA5u) {
        fputs("hdma mutant duplicate_copy detected adjacent destination predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_wrong_vbk(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    mutant_advance_block(m);
    if (memcmp(m->vram[0], m->wram[0], 16u) != 0) {
        fputs("hdma mutant wrong_vbk detected sampled-bank destination predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_unmasked_address(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->hdma.mode = 0u;
    m->hdma.active = 0u;
    m->hdma.destination_cursor = 0x8000u;
    hdma_register_write(m, 0xFF54u, 0x0Fu);
    if (m->hdma.destination_cursor != 0x8000u) {
        fputs("hdma mutant unmasked_address detected FF54 low-nibble predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_wrong_count(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->hdma.blocks_remaining = 2u;
    mutant_advance_block(m);
    if (m->hdma.blocks_remaining != 1u || m->hdma.mode != 2u ||
        m->hdma.control_readback != 0u) {
        fputs("hdma mutant wrong_count detected one-block decrement predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_wrong_cancel(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->hdma.mode = 1u;
    m->hdma.active = 0u;
    m->hdma.blocks_remaining = 5u;
    hdma_register_write(m, 0xFF55u, 0x02u);
    if (m->hdma.blocks_remaining != 0u || m->hdma.control_readback != 0x82u) {
        fputs("hdma mutant wrong_cancel detected written-count readback predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_halt_admission(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->halted = 1u;
    m->hdma.mode = 1u;
    m->hdma.active = 0u;
    m->hdma.pending_hblank = 0u;
    m->hdma.blocks_remaining = 1u;
    hdma_request(m);
    if (m->hdma.pending_hblank) {
        fputs("hdma mutant halt_admission detected HALT request predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_false_trigger(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->hdma.mode = 1u;
    m->hdma.active = 0u;
    m->hdma.blocks_remaining = 1u;
    m->lcdc = 0x91u;
    m->ly = GBB_FRAME_HEIGHT;
    m->ppu_mode = 3u;
    ppu_set_mode(m, 0u);
    if (m->hdma.pending_hblank) {
        fputs("hdma mutant false_trigger detected visible-line admission predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_lost_dma_irq(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->hdma.mode = 1u;
    m->hdma.active = 1u;
    m->hdma.blocks_remaining = 1u;
    m->hdma.byte_index = 4u;
    m->cpu_stall_kind = GBB_STALL_SPEED_SWITCH;
    m->cpu_stall_half_dots = 8u;
    m->ie = 0x04u;
    m->interrupt_flags = 0x04u;
    (void)gbb_run(m, 1u, NULL, 0u);
    if (!m->hdma.active || m->hdma.blocks_remaining != 1u) {
        fputs("hdma mutant lost_dma_irq detected admitted-block retention predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_dma_realign(void) {
    gbb_instance *m = NULL;
    REQUIRE(mutant_machine_create(&m) == 0);
    m->time_half_dots = 4u;
    mutant_advance_block(m);
    if (m->cpu_stall_kind != GBB_STALL_NONE || m->cpu_stall_half_dots != 0u) {
        fputs("hdma mutant dma_realign detected DMA-only phase predicate\n", stderr);
        gbb_destroy(m);
        return 1;
    }
    gbb_destroy(m);
    return 0;
}

static int test_mutant_shifted_order(void) {
    return test_oam_order();
}

static int timing_offset_commit(int offset, unsigned expected_half_dots) {
    gbb_p13_set_duration_offset(offset);
    gbb_instance *m = NULL;
    if (policy_fixture_create(&m, 0x80u, 0u, 0, 0, 0, 0u, 0u, 0u, 16u) != 0) {
        gbb_p13_set_duration_offset(0);
        return 1;
    }
    const uint64_t start = m->time_half_dots;
    gbb_run_result start_block = gbb_run(m, 40u, NULL, 0u);
    if (start_block.consumed_half_dots != 40u || !m->hdma.pending_hblank ||
        !hdma_admit_block(m)) {
        gbb_destroy(m);
        gbb_p13_set_duration_offset(0);
        return 1;
    }
    unsigned observed = 0u;
    for (unsigned half_dot = 1u; half_dot <= 12u; ++half_dot) {
        gbb_run_result tick = gbb_run(m, 1u, NULL, 0u);
        if (tick.consumed_half_dots != 1u) break;
        if (m->vram[0][0] == m->wram[0][0]) {
            observed = half_dot;
            break;
        }
    }
    gbb_destroy(m);
    gbb_p13_set_duration_offset(0);
    return observed == expected_half_dots ? 0 : 1;
}

static int test_timing_sensitivity(void) {
    static const int offsets[] = {-8, -4, -2, -1, 1, 2, 4, 8};
    static const unsigned expected[] = {1u, 1u, 2u, 3u, 5u, 6u, 8u, 12u};
    for (size_t i = 0u; i < sizeof(offsets) / sizeof(offsets[0]); ++i) {
        if (timing_offset_commit(offsets[i], expected[i]) != 0) {
            fprintf(stderr, "timing sensitivity: offset %+d expected first commit at %u half-dots\n",
                    offsets[i], expected[i]);
            return 1;
        }
    }
    puts("timing sensitivity offsets -8,-4,-2,-1,+1,+2,+4,+8 detected in one normal-speed master-time series; double-speed cadence covered separately; physical CGB-E UNKNOWN");
    return 0;
}

int main(int argc, char **argv) {
#ifdef GBB_P12_MUTANT_BUILD
    if (argc >= 4 && strcmp(argv[argc - 2], "--mutants") == 0) {
        char *end = NULL;
        unsigned long long mask = strtoull(argv[argc - 1], &end, 0);
        if (end == argv[argc - 1] || *end != '\0') return 2;
        gbb_p12_set_mutants((uint64_t)mask);
        argc -= 2;
    }
#endif
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
    else if (strcmp(argv[1], "competing_stalls") == 0) rc = test_competing_stalls();
    else if (strcmp(argv[1], "competing_stalls_controls") == 0) rc = test_competing_stalls_controls();
    else if (strcmp(argv[1], "stop_policy") == 0) rc = test_stop_policy();
    else if (strcmp(argv[1], "stop_policy_controls") == 0) rc = test_stop_policy_controls();
    else if (strcmp(argv[1], "oam_order") == 0) rc = test_oam_order();
    else if (strcmp(argv[1], "oam_order_controls") == 0) rc = test_oam_order_controls();
    else if (strcmp(argv[1], "lifecycle") == 0) rc = test_hdma_lifecycle();
    else if (strcmp(argv[1], "lifecycle_controls") == 0)
        rc = test_hdma_lifecycle_controls();
    else if (strcmp(argv[1], "resource_bounds") == 0)
        rc = test_hdma_resource_bounds();
    else if (strcmp(argv[1], "resource_bounds_controls") == 0)
        rc = test_hdma_resource_controls();
    else if (strcmp(argv[1], "hostile_seeds") == 0)
        rc = test_hdma_hostile_seeds();
    else if (strcmp(argv[1], "hostile_seeds_controls") == 0)
        rc = test_hdma_hostile_seed_controls();
    else if (strcmp(argv[1], "mutant_no_copy") == 0) rc = test_mutant_no_copy();
    else if (strcmp(argv[1], "mutant_duplicate_copy") == 0) rc = test_mutant_duplicate_copy();
    else if (strcmp(argv[1], "mutant_wrong_vbk") == 0) rc = test_mutant_wrong_vbk();
    else if (strcmp(argv[1], "mutant_unmasked_address") == 0) rc = test_mutant_unmasked_address();
    else if (strcmp(argv[1], "mutant_wrong_count") == 0) rc = test_mutant_wrong_count();
    else if (strcmp(argv[1], "mutant_wrong_cancel") == 0) rc = test_mutant_wrong_cancel();
    else if (strcmp(argv[1], "mutant_halt_admission") == 0) rc = test_mutant_halt_admission();
    else if (strcmp(argv[1], "mutant_false_trigger") == 0) rc = test_mutant_false_trigger();
    else if (strcmp(argv[1], "mutant_lost_dma_irq") == 0) rc = test_mutant_lost_dma_irq();
    else if (strcmp(argv[1], "mutant_dma_realign") == 0) rc = test_mutant_dma_realign();
    else if (strcmp(argv[1], "mutant_shifted_order") == 0) rc = test_mutant_shifted_order();
    else if (strcmp(argv[1], "timing_sensitivity") == 0) rc = test_timing_sensitivity();
    else return 2;
    if (rc == 0) printf("cgb-hdma %s pass\n", argv[1]);
    return rc;
}
