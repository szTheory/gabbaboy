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
    f->machine->lcdc = 0u; /* Hold the PPU until the guest has programmed FF51-FF55. */
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
    int saw_late_timing = 0;
    int saw_edge = 0;
    uint64_t edge_at = UINT64_MAX;
    for (size_t i = 0; i < gbb_test_observer_count(m); ++i) {
        if (bus[i].access == 2u &&
            ((is_ld_sp && (bus[i].address == 0xC100u || bus[i].address == 0xC101u)) ||
             (!is_ld_sp && bus[i].address == 0xC100u))) {
            ++late_writes;
            if (bus[i].address == f.late_address &&
                bus[i].time_half_dots == start + expected_late)
                saw_late_timing = 1;
        }
    }
    for (size_t i = 0; i < gbb_test_ppu_observer_count(m); ++i) {
        if (ppu[i].address == 0xFF41u && ppu[i].access == 4u && ppu[i].value == 0u) {
            saw_edge = 1;
            edge_at = ppu[i].time_half_dots;
        }
    }
    REQUIRE(late_writes == (is_ld_sp ? 2u : 1u) && saw_late_timing);
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
    no_edge.machine->lcdc = 0x91u;
    no_edge.machine->ppu_mode = 3u;
    no_edge.machine->ppu_transfer_age = 12u;
    no_edge.machine->ppu_fifo_count = 0u;
    gbb_run_result no_edge_run = gbb_run(no_edge.machine,
        no_edge.instruction_cost + 64u, NULL, 0u);
    REQUIRE(no_edge_run.consumed_half_dots == no_edge.instruction_cost &&
            no_edge.machine->vram[0][0] != no_edge.source[0]);
    gbb_destroy(no_edge.machine);

    hdma_fixture disabled;
    REQUIRE(fixture_create(&disabled, 1, 0, 0, 1) == 0);
    gbb_run_result disabled_run = gbb_run(disabled.machine,
        disabled.instruction_cost + 64u, NULL, 0u);
    REQUIRE(disabled_run.consumed_half_dots == disabled.instruction_cost &&
            disabled.machine->vram[0][0] != disabled.source[0]);
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
    gbb_diagnostic_record diagnostics[GBB_DIAGNOSTIC_OPERATION_RESERVE + 1u];
    memset(diagnostics, 0x5A, sizeof(diagnostics));
    gbb_run_result run = gbb_run_ex(f.machine, f.instruction_cost + 64u,
        trace, 1u, diagnostics, GBB_DIAGNOSTIC_OPERATION_RESERVE);
    REQUIRE(run.consumed_half_dots == f.instruction_cost + 64u &&
            f.machine->time_half_dots == run.consumed_half_dots + HDMA_SETUP_HALF_DOTS);
    REQUIRE(run.trace_count == 1u && trace[1].pc == UINT16_C(0xA5A5));
    const uint8_t *after = (const uint8_t *)&diagnostics[GBB_DIAGNOSTIC_OPERATION_RESERVE];
    for (size_t i = 0u; i < sizeof(diagnostics[0]); ++i) REQUIRE(after[i] == 0x5Au);
    gbb_destroy(f.machine);

    REQUIRE(fixture_create(&f, 1, 0, 1, 1) == 0);
    gbb_audio_frame frames[8];
    memset(frames, 0x6B, sizeof(frames));
    size_t frame_count = 0u;
    run = gbb_run_audio(f.machine, f.instruction_cost + 64u,
        frames, 7u, &frame_count);
    REQUIRE(run.consumed_half_dots == f.instruction_cost + 64u && frame_count <= 7u);
    const uint8_t *audio_sentinel = (const uint8_t *)&frames[7];
    for (size_t i = 0u; i < sizeof(frames[0]); ++i) REQUIRE(audio_sentinel[i] == 0x6Bu);
    gbb_destroy(f.machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    int rc;
    if (strcmp(argv[1], "ld_sp") == 0) rc = test_ld_sp();
    else if (strcmp(argv[1], "cb") == 0) rc = test_cb();
    else if (strcmp(argv[1], "controls") == 0) rc = test_controls();
    else if (strcmp(argv[1], "partition") == 0) rc = test_partition();
    else if (strcmp(argv[1], "outputs") == 0) rc = test_outputs();
    else return 2;
    if (rc == 0) printf("cgb-hdma %s pass\n", argv[1]);
    return rc;
}
