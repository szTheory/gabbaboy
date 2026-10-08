#include "gabbaboy/gabbaboy.h"

#include <stdlib.h>
#include <string.h>

#define GBB_INPUT_EVENT_CAPACITY 64u
#define GBB_DIAGNOSTIC_OPERATION_RESERVE 16u
#define GBB_FRAME_WIDTH 160u
#define GBB_FRAME_HEIGHT 144u
#define GBB_FRAME_PIXELS (GBB_FRAME_WIDTH * GBB_FRAME_HEIGHT)
#define GBB_OAM_BYTES 160u
#define GBB_DMA_BYTE_PERIOD_HALF_DOTS 8u
#define GBB_LINE_OBJECT_LIMIT 10u
#define GBB_PPU_FIFO_CAPACITY 16u

typedef struct gbb_test_dma_event gbb_test_dma_event;

struct gbb_instance {
    uint8_t *rom;
    size_t rom_size;
    uint8_t wram[8192];
    uint8_t hram[127];
    uint8_t vram[8192];
    uint8_t oam[GBB_OAM_BYTES];
    uint8_t frame_working[GBB_FRAME_PIXELS];
    uint8_t frame_completed[GBB_FRAME_PIXELS];
    uint64_t frame_generation;
    uint64_t frame_completion_half_dots;
    uint16_t ppu_dot;
    uint8_t ppu_half_phase;
    uint8_t ppu_mode;
    uint8_t ppu_stat_line;
    uint8_t ppu_fifo[GBB_PPU_FIFO_CAPACITY];
    uint8_t ppu_fifo_head, ppu_fifo_count;
    uint8_t ppu_fetch_stage, ppu_fetch_phase;
    uint16_t ppu_fetch_enqueued;
    uint8_t ppu_transfer_age, ppu_output_x, ppu_scroll_discard, ppu_fine_scroll;
    uint8_t ppu_mode3_stall, ppu_window_started, ppu_transfer_complete;
    uint16_t ppu_objects_stalled;
    uint32_t ppu_object_tiles_fetched;
    uint8_t ppu_selected_objects[GBB_LINE_OBJECT_LIMIT];
    uint8_t ppu_selected_y[GBB_LINE_OBJECT_LIMIT];
    uint8_t ppu_selected_x[GBB_LINE_OBJECT_LIMIT];
    uint8_t ppu_selected_tile[GBB_LINE_OBJECT_LIMIT];
    uint8_t ppu_selected_attributes[GBB_LINE_OBJECT_LIMIT];
    uint8_t ppu_selected_object_count;
    uint8_t ppu_scan_index;
    uint8_t ppu_window_line;
    uint8_t ppu_window_line_drawn;
    uint8_t dma_register, dma_page, dma_pending_page, dma_index, dma_phase;
    int dma_active, dma_start_pending, dma_cpu_blocked;
    uint8_t lcdc, scy, scx, ly, lyc, bgp, obp0, obp1, wy, wx;
    uint8_t joypad_select;
    uint8_t joypad_buttons;
    uint8_t a, f, b, c, d, e, h, l;
    uint8_t div, stat, tima, tma, tac;
    uint8_t serial_data, serial_control, serial_bits;
    uint8_t ie, interrupt_flags;
    uint8_t ime_delay;
    int ime;
    uint8_t divider_phase;
    uint16_t divider_counter;
    int timer_signal;
    int timer_reload_pending;
    uint8_t timer_reload_remaining;
    uint64_t timer_reloaded_at;
    uint64_t instruction_start_half_dots;
    uint16_t serial_edge_remaining;
    int serial_active, serial_unsupported;
    int halted, stopped, halt_bug;
    uint16_t pc, sp;
    uint64_t time_half_dots;
    gbb_input_event input_events[GBB_INPUT_EVENT_CAPACITY];
    size_t input_event_count;
    uint16_t lockup_pc;
    uint8_t lockup_opcode;
    int locked;
    struct gbb_test_bus_event *test_events;
    size_t test_event_capacity;
    size_t test_event_count;
    struct gbb_test_bus_event *test_ppu_events;
    size_t test_ppu_event_capacity;
    size_t test_ppu_event_count;
    gbb_test_dma_event *test_dma_events;
    size_t test_dma_event_capacity;
    size_t test_dma_event_count;
    int loaded;
    gbb_diagnostic_record *diagnostic_output;
    size_t diagnostic_output_capacity;
    size_t diagnostic_output_count;
    gbb_diagnostic_record *diagnostic_operation;
    size_t diagnostic_operation_count;
    uint16_t diagnostic_pc;
    uint8_t diagnostic_opcode;
};

static uint8_t diagnostic_timer_state(const gbb_instance *m) {
    return (uint8_t)((m->tac & 7u) | (m->timer_reload_pending ? 0x08u : 0u) |
                     (m->timer_signal ? 0x10u : 0u));
}

static void diagnostic_add(gbb_instance *m, gbb_diagnostic_kind kind,
                           uint64_t time, uint16_t address, uint8_t value) {
    if (m->diagnostic_operation == NULL ||
        m->diagnostic_operation_count >= GBB_DIAGNOSTIC_OPERATION_RESERVE) return;
    gbb_diagnostic_record *record = &m->diagnostic_operation[m->diagnostic_operation_count++];
    record->time_half_dots = time;
    record->kind = kind;
    record->pc = m->diagnostic_pc;
    record->opcode = m->diagnostic_opcode;
    record->address = address;
    record->value = value;
    record->timer_state = diagnostic_timer_state(m);
}

static void diagnostic_begin(gbb_instance *m, gbb_diagnostic_record records[GBB_DIAGNOSTIC_OPERATION_RESERVE], uint16_t pc, uint8_t opcode) {
    if (m->diagnostic_output == NULL) return;
    m->diagnostic_operation = records;
    m->diagnostic_operation_count = 0;
    m->diagnostic_pc = pc;
    m->diagnostic_opcode = opcode;
    diagnostic_add(m, GBB_DIAGNOSTIC_INSTRUCTION, m->time_half_dots, 0, opcode);
}

static void diagnostic_commit(gbb_instance *m) {
    if (m->diagnostic_output == NULL || m->diagnostic_operation == NULL) return;
    memcpy(m->diagnostic_output + m->diagnostic_output_count, m->diagnostic_operation,
           m->diagnostic_operation_count * sizeof(*m->diagnostic_output));
    m->diagnostic_output_count += m->diagnostic_operation_count;
    m->diagnostic_operation = NULL;
    m->diagnostic_operation_count = 0;
}

typedef struct gbb_test_bus_event {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

struct gbb_test_dma_event {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
};

void gbb_test_observer_set(gbb_instance *m, gbb_test_bus_event *events, size_t capacity) {
    if (m == NULL) return;
    m->test_events = events;
    m->test_event_capacity = capacity;
    m->test_event_count = 0;
}

size_t gbb_test_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_event_count;
}

void gbb_test_ppu_observer_set(gbb_instance *m, gbb_test_bus_event *events,
                               size_t capacity) {
    if (m == NULL) return;
    m->test_ppu_events = events;
    m->test_ppu_event_capacity = capacity;
    m->test_ppu_event_count = 0;
}

size_t gbb_test_ppu_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_ppu_event_count;
}

void gbb_test_dma_observer_set(gbb_instance *m, gbb_test_dma_event *events,
                               size_t capacity) {
    if (m == NULL) return;
    m->test_dma_events = events;
    m->test_dma_event_capacity = capacity;
    m->test_dma_event_count = 0;
}

size_t gbb_test_dma_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_dma_event_count;
}

static void observe_dma(gbb_instance *m, uint16_t address, uint8_t access,
                        uint8_t value) {
    if (m->test_dma_events != NULL &&
        m->test_dma_event_count < m->test_dma_event_capacity) {
        gbb_test_dma_event *event = &m->test_dma_events[m->test_dma_event_count++];
        event->time_half_dots = m->time_half_dots;
        event->address = address;
        event->access = access;
        event->value = value;
    }
}

static void observe_ppu(gbb_instance *m, uint16_t address, uint8_t access,
                        uint8_t value) {
    if (m->test_ppu_events != NULL &&
        m->test_ppu_event_count < m->test_ppu_event_capacity) {
        gbb_test_bus_event *event = &m->test_ppu_events[m->test_ppu_event_count++];
        memset(event, 0, sizeof(*event));
        event->time_half_dots = m->time_half_dots;
        event->address = address;
        event->access = access;
        event->value = value;
    }
}

static void ppu_update_stat_line(gbb_instance *m);

static void ppu_set_mode(gbb_instance *m, uint8_t mode) {
    if (m->ppu_mode != mode) {
        m->ppu_mode = mode;
        observe_ppu(m, 0xFF41, 4, mode);
        ppu_update_stat_line(m);
    }
}

static void ppu_update_stat_line(gbb_instance *m) {
    int line = 0;
    if ((m->lcdc & 0x80u) != 0) {
        line = (((m->ppu_mode == 0u) && ((m->stat & 0x08u) != 0)) ||
                ((m->ppu_mode == 1u) && ((m->stat & 0x10u) != 0)) ||
                ((m->ppu_mode == 2u) && ((m->stat & 0x20u) != 0)) ||
                ((m->ly == m->lyc) && ((m->stat & 0x40u) != 0)));
    }
    if (line && !m->ppu_stat_line) {
        m->interrupt_flags |= 0x02u;
        observe_ppu(m, 0xFF0F, 5, (uint8_t)(0xE0u | m->interrupt_flags));
    }
    m->ppu_stat_line = (uint8_t)line;
}

static void observe_bus(gbb_instance *m, uint64_t offset, uint16_t address, uint8_t access, uint8_t value) {
    if (access == 1) diagnostic_add(m, GBB_DIAGNOSTIC_BUS_READ, m->time_half_dots + offset, address, value);
    else if (access == 2) diagnostic_add(m, GBB_DIAGNOSTIC_BUS_WRITE, m->time_half_dots + offset, address, value);
    if (m->test_events != NULL && m->test_event_count < m->test_event_capacity) {
        gbb_test_bus_event *event = &m->test_events[m->test_event_count++];
        memset(event, 0, sizeof(*event));
        event->time_half_dots = m->time_half_dots + offset;
        event->address = address;
        event->access = access;
        event->value = value;
    }
}

#define GBB_MAX_ROM_SIZE ((size_t)8u * 1024u * 1024u)

static void reset_state(gbb_instance *m) {
    m->a = 0x01;
    m->f = m->rom != NULL && m->rom_size > 0x14Du && m->rom[0x14Du] != 0 ? 0xB0u : 0x80u;
    m->b = 0x00; m->c = 0x13;
    m->d = 0x00; m->e = 0xD8; m->h = 0x01; m->l = 0x4D;
    m->pc = 0x0100; m->sp = 0xFFFE;
    m->div = 0xAB; m->stat = 0;
    m->tima = 0; m->tma = 0; m->tac = 0;
    m->serial_data = 0; m->serial_control = 0x7Eu; m->serial_bits = 0;
    m->ie = 0;
    m->interrupt_flags = 0;
    m->ime_delay = 0;
    m->ime = 0;
    m->divider_phase = 0;
    m->divider_counter = 0xAB00u;
    m->timer_signal = 0;
    m->timer_reload_pending = 0;
    m->timer_reload_remaining = 0;
    m->timer_reloaded_at = UINT64_MAX;
    m->instruction_start_half_dots = 0;
    m->serial_edge_remaining = 0;
    m->serial_active = 0;
    m->serial_unsupported = 0;
    m->dma_register = 0xFFu;
    m->dma_page = 0;
    m->dma_pending_page = 0;
    m->dma_index = 0;
    m->dma_phase = 0;
    m->dma_active = 0;
    m->dma_start_pending = 0;
    m->dma_cpu_blocked = 0;
    m->halted = 0;
    m->stopped = 0;
    m->halt_bug = 0;
    memset(m->wram, 0, sizeof(m->wram));
    memset(m->hram, 0, sizeof(m->hram));
    memset(m->vram, 0, sizeof(m->vram));
    memset(m->oam, 0, sizeof(m->oam));
    memset(m->frame_working, 0, sizeof(m->frame_working));
    memset(m->frame_completed, 0, sizeof(m->frame_completed));
    m->frame_generation = 0;
    m->frame_completion_half_dots = 0;
    m->ppu_dot = 0;
    m->ppu_half_phase = 0;
    m->ppu_mode = 2;
    m->ppu_stat_line = 0;
    memset(m->ppu_fifo, 0, sizeof(m->ppu_fifo));
    m->ppu_fifo_head = 0;
    m->ppu_fifo_count = 0;
    m->ppu_fetch_stage = 0;
    m->ppu_fetch_phase = 0;
    m->ppu_fetch_enqueued = 0;
    m->ppu_transfer_age = 0;
    m->ppu_output_x = 0;
    m->ppu_scroll_discard = 0;
    m->ppu_fine_scroll = 0;
    m->ppu_mode3_stall = 0;
    m->ppu_window_started = 0;
    m->ppu_transfer_complete = 0;
    m->ppu_objects_stalled = 0;
    m->ppu_object_tiles_fetched = 0;
    memset(m->ppu_selected_objects, 0, sizeof(m->ppu_selected_objects));
    m->ppu_selected_object_count = 0;
    m->ppu_window_line = 0;
    m->ppu_window_line_drawn = 0;
    m->lcdc = 0x91;
    m->scy = 0;
    m->scx = 0;
    m->ly = 0;
    m->lyc = 0;
    m->bgp = 0xFC;
    m->obp0 = 0xFF;
    m->obp1 = 0xFF;
    m->wy = 0;
    m->wx = 0;
    m->joypad_select = 0x30;
    m->joypad_buttons = 0;
    m->time_half_dots = 0;
    m->input_event_count = 0;
    m->lockup_pc = 0;
    m->lockup_opcode = 0;
    m->locked = 0;
}

static uint8_t joypad_value(const gbb_instance *m) {
    uint8_t lines = 0x0Fu;
    if ((m->joypad_select & 0x20u) == 0)
        lines &= (uint8_t)~((m->joypad_buttons >> 4) & 0x0Fu);
    if ((m->joypad_select & 0x10u) == 0)
        lines &= (uint8_t)~(m->joypad_buttons & 0x0Fu);
    return (uint8_t)(0xC0u | m->joypad_select | lines);
}

/* Request JOYP IF at the ordered software boundary that changes the selected
 * active-low pins. Pin settling, bounce, and CPU-B sampling latency are outside
 * this event-boundary model. */
static void joypad_request_falling_edge(gbb_instance *m, uint8_t previous) {
    uint8_t current = (uint8_t)(joypad_value(m) & 0x0Fu);
    if ((previous & (uint8_t)~current & 0x0Fu) != 0)
        m->interrupt_flags |= 0x10u;
}

static int cpu_vram_access_allowed(const gbb_instance *m) {
    return (m->lcdc & 0x80u) == 0 || m->ppu_mode != 3u;
}

static int cpu_oam_access_allowed(const gbb_instance *m) {
    return (m->lcdc & 0x80u) == 0 || m->ppu_mode == 0u || m->ppu_mode == 1u;
}

static int cpu_hram_address(uint16_t address) {
    return address >= 0xFF80u && address <= 0xFFFEu;
}

static void ppu_begin_object_scan(gbb_instance *m);

static uint8_t read8(const gbb_instance *m, uint16_t address) {
    if (m->dma_active && m->dma_cpu_blocked &&
        !cpu_hram_address(address) && address != 0xFF46u) return 0xFFu;
    if (address == 0xFF00) return joypad_value(m);
    if (address == 0xFF04) return m->div;
    if (address == 0xFF05) return m->tima;
    if (address == 0xFF06) return m->tma;
    if (address == 0xFF07) return (uint8_t)(0xF8u | m->tac);
    if (address == 0xFF01) return m->serial_data;
    if (address == 0xFF02) return (uint8_t)(0x7Eu | m->serial_control);
    if (address == 0xFF40) return m->lcdc;
    if (address == 0xFF41)
        return (uint8_t)(0x80u | (m->stat & 0x78u) |
                         (m->ly == m->lyc ? 0x04u : 0u) | m->ppu_mode);
    if (address == 0xFF42) return m->scy;
    if (address == 0xFF43) return m->scx;
    if (address == 0xFF44) return m->ly;
    if (address == 0xFF45) return m->lyc;
    if (address == 0xFF46) return m->dma_register;
    if (address == 0xFF47) return m->bgp;
    if (address == 0xFF48) return m->obp0;
    if (address == 0xFF49) return m->obp1;
    if (address == 0xFF4A) return m->wy;
    if (address == 0xFF4B) return m->wx;
    if (address == 0xFF0F) return (uint8_t)(0xE0u | m->interrupt_flags);
    if (address == 0xFFFF) return (uint8_t)(0xE0u | m->ie);
    if (address >= 0x8000 && address <= 0x9FFF)
        return cpu_vram_access_allowed(m) ? m->vram[address - 0x8000] : 0xFF;
    if (address >= 0xFE00 && address <= 0xFE9F)
        return cpu_oam_access_allowed(m) ? m->oam[address - 0xFE00] : 0xFF;
    if (address < m->rom_size) return m->rom[address];
    if (address >= 0xC000 && address <= 0xDFFF) return m->wram[address - 0xC000];
    if (address >= 0xE000 && address <= 0xFDFF) return m->wram[address - 0xE000];
    if (address >= 0xFF80 && address <= 0xFFFE) return m->hram[address - 0xFF80];
    return 0xFF;
}

static void advance_devices_to(gbb_instance *m, uint64_t target);

static uint8_t bus_read(gbb_instance *m, uint16_t address, uint64_t offset) {
    advance_devices_to(m, m->instruction_start_half_dots + offset);
    uint8_t value = read8(m, address);
    observe_bus(m, 0, address, 1, value);
    return value;
}

static unsigned timer_bit(uint8_t tac) {
    static const uint8_t bits[4] = {9, 3, 5, 7};
    return bits[tac & 3u];
}

static int timer_input(const gbb_instance *m) {
    return (m->tac & 4u) != 0 && ((m->divider_counter >> timer_bit(m->tac)) & 1u) != 0;
}

static void timer_increment(gbb_instance *m, uint64_t at) {
    if (m->timer_reload_pending) return;
    if (m->tima == 0xFFu) {
        m->tima = 0;
        m->timer_reload_pending = 1;
        m->timer_reload_remaining = 8u;
        observe_bus(m, 0, 0xFF05, 3, m->tima);
        diagnostic_add(m, GBB_DIAGNOSTIC_TIMER, at, 0xFF05, m->tima);
    } else {
        ++m->tima;
        diagnostic_add(m, GBB_DIAGNOSTIC_TIMER, at, 0xFF05, m->tima);
    }
}

static void timer_set_signal(gbb_instance *m, int next, uint64_t at) {
    if (m->timer_signal && !next) timer_increment(m, at);
    m->timer_signal = next;
}

static void write8(gbb_instance *m, uint16_t address, uint8_t value) {
    if (m->dma_active && m->dma_cpu_blocked &&
        !cpu_hram_address(address) && address != 0xFF46u) return;
    if (address >= 0x8000 && address <= 0x9FFF) {
        if (cpu_vram_access_allowed(m)) m->vram[address - 0x8000] = value;
    }
    else if (address >= 0xFE00 && address <= 0xFE9F) {
        if (cpu_oam_access_allowed(m)) m->oam[address - 0xFE00] = value;
    }
    else if (address == 0xFF00) {
        uint8_t previous = (uint8_t)(joypad_value(m) & 0x0Fu);
        m->joypad_select = (uint8_t)(value & 0x30u);
        joypad_request_falling_edge(m, previous);
    }
    else if (address == 0xFF40) {
        uint8_t old = m->lcdc;
        m->lcdc = value;
        if ((value & 0x80u) == 0) {
            m->ppu_dot = 0;
            m->ppu_half_phase = 0;
            m->ly = 0;
            ppu_set_mode(m, 0);
            m->ppu_selected_object_count = 0;
            m->ppu_window_line = 0;
            m->ppu_window_line_drawn = 0;
            m->ppu_transfer_complete = 0;
            m->ppu_fifo_count = 0;
            memset(m->frame_working, 0, sizeof(m->frame_working));
            ppu_update_stat_line(m);
        } else if ((old & 0x80u) == 0) {
            m->ppu_dot = 0;
            m->ppu_half_phase = 0;
            m->ly = 0;
            ppu_set_mode(m, 2);
            m->ppu_selected_object_count = 0;
            m->ppu_window_line = 0;
            m->ppu_window_line_drawn = 0;
            ppu_begin_object_scan(m);
        }
    }
    else if (address == 0xFF41) {
        m->stat = (uint8_t)(value & 0x78u);
        ppu_update_stat_line(m);
    }
    else if (address == 0xFF42) m->scy = value;
    else if (address == 0xFF43) m->scx = value;
    else if (address == 0xFF44) { /* LY is read-only in the guest interface. */ }
    else if (address == 0xFF45) {
        m->lyc = value;
        ppu_update_stat_line(m);
    }
    else if (address == 0xFF46) {
        m->dma_register = value;
        m->dma_pending_page = value;
        m->dma_start_pending = 1;
    }
    else if (address == 0xFF47) m->bgp = value;
    else if (address == 0xFF48) m->obp0 = value;
    else if (address == 0xFF49) m->obp1 = value;
    else if (address == 0xFF4A) m->wy = value;
    else if (address == 0xFF4B) m->wx = value;
    else if (address == 0xFF04) {
        m->divider_counter = 0; m->div = 0; m->divider_phase = 0;
        timer_set_signal(m, timer_input(m), m->time_half_dots);
    }
    else if (address == 0xFF05) {
        if (m->time_half_dots == m->timer_reloaded_at) { /* reload wins this sampled write */ }
        else { m->tima = value; m->timer_reload_pending = 0; }
    }
    else if (address == 0xFF06) {
        m->tma = value;
        if (m->time_half_dots == m->timer_reloaded_at) m->tima = value;
    }
    else if (address == 0xFF07) {
        m->tac = (uint8_t)(value & 7u);
        timer_set_signal(m, timer_input(m), m->time_half_dots);
    }
    else if (address == 0xFF01) {
        if (m->serial_active) m->serial_unsupported = 1;
        else m->serial_data = value;
    }
    else if (address == 0xFF02) {
        if (m->serial_active) {
            m->serial_unsupported = 1;
        } else {
            m->serial_control = (uint8_t)(value & 0x81u);
            if (value & 0x80u) {
                m->serial_active = 1;
                m->serial_bits = 0;
                if (value & 1u) m->serial_edge_remaining = 1024u;
            }
        }
    }
    else if (address == 0xFF0F) m->interrupt_flags = (uint8_t)(value & 0x1Fu);
    else if (address == 0xFFFF) m->ie = (uint8_t)(value & 0x1Fu);
    else if (address >= 0xC000 && address <= 0xDFFF) m->wram[address - 0xC000] = value;
    else if (address >= 0xE000 && address <= 0xFDFF) m->wram[address - 0xE000] = value;
    else if (address >= 0xFF80 && address <= 0xFFFE) m->hram[address - 0xFF80] = value;
}

static void bus_write(gbb_instance *m, uint16_t address, uint8_t value, uint64_t offset) {
    uint64_t timestamp = m->instruction_start_half_dots + offset;
    /* TMA feeds the reload when the write shares its exact reload timestamp. */
    if (address == 0xFF06 && m->timer_reload_pending && timestamp >= m->time_half_dots &&
        timestamp - m->time_half_dots == m->timer_reload_remaining)
        m->tma = value;
    advance_devices_to(m, timestamp);
    observe_bus(m, 0, address, 2, value);
    write8(m, address, value);
}

static int read_supported(uint16_t address) {
    return address < 0xA000 || (address >= 0xFE00 && address <= 0xFE9F) ||
           address == 0xFF00 || address == 0xFF01 || address == 0xFF02 ||
           (address >= 0xFF04 && address <= 0xFF07) || address == 0xFF0F || address == 0xFFFF ||
           (address >= 0xFF40 && address <= 0xFF46) ||
           (address >= 0xFF47 && address <= 0xFF4B) ||
           (address >= 0xC000 && address <= 0xDFFF) ||
           (address >= 0xE000 && address <= 0xFDFF) ||
           (address >= 0xFF80 && address <= 0xFFFE);
}

static uint16_t hl(const gbb_instance *m) { return (uint16_t)(((uint16_t)m->h << 8) | m->l); }
static unsigned pending_interrupt(const gbb_instance *m);

static void shift_external_serial(gbb_instance *m, uint8_t bit) {
    if (!m->serial_active || (m->serial_control & 1u) != 0) return;
    m->serial_data = (uint8_t)((m->serial_data << 1) | bit);
    if (++m->serial_bits == 8u) {
        m->serial_active = 0;
        m->serial_control &= 1u;
        m->interrupt_flags |= 0x08u;
    }
}

static void apply_input_events_now(gbb_instance *m) {
    while (m->input_event_count != 0 &&
           m->input_events[0].at_half_dots == m->time_half_dots) {
        gbb_input_event event = m->input_events[0];
        --m->input_event_count;
        if (m->input_event_count != 0)
            memmove(m->input_events, m->input_events + 1,
                    m->input_event_count * sizeof(m->input_events[0]));
        if (event.kind == GBB_INPUT_STOP_WAKE) {
            if (m->stopped && event.value == 1u) m->stopped = 0;
        } else if (event.kind == GBB_INPUT_SERIAL_EDGE) {
            shift_external_serial(m, event.value);
        } else if (event.kind == GBB_INPUT_BUTTON_PRESS) {
            uint8_t previous = (uint8_t)(joypad_value(m) & 0x0Fu);
            m->joypad_buttons |= (uint8_t)(1u << event.value);
            joypad_request_falling_edge(m, previous);
        } else if (event.kind == GBB_INPUT_BUTTON_RELEASE) {
            uint8_t previous = (uint8_t)(joypad_value(m) & 0x0Fu);
            m->joypad_buttons &= (uint8_t)~(1u << event.value);
            joypad_request_falling_edge(m, previous);
        }
    }
}

static uint16_t instruction_address(const gbb_instance *m, uint16_t pc, unsigned offset) {
    if (m->halt_bug && offset != 0) --offset;
    return (uint16_t)(pc + offset);
}

static uint8_t instruction_byte(const gbb_instance *m, uint16_t pc, unsigned offset) {
    return read8(m, instruction_address(m, pc, offset));
}

static uint8_t ppu_tile_color(const gbb_instance *m, uint8_t tile,
                              unsigned row, unsigned column, int object) {
    int tile_base;
    if (object || (m->lcdc & 0x10u) != 0) {
        tile_base = (int)tile * 16;
    } else {
        tile_base = 0x1000 + (int)(int8_t)tile * 16;
    }
    if (tile_base < 0 || tile_base + 15 >= 0x1800 || row >= 8u || column >= 8u)
        return 0;
    unsigned address = (unsigned)tile_base + row * 2u;
    uint8_t bit = (uint8_t)(7u - column);
    uint8_t low = m->vram[address];
    uint8_t high = m->vram[address + 1u];
    return (uint8_t)(((low >> bit) & 1u) | (((high >> bit) & 1u) << 1));
}

static int ppu_window_visible_at(const gbb_instance *m, unsigned x) {
    if ((m->lcdc & 0x21u) != 0x21u || m->ly < m->wy || m->wx > 166u)
        return 0;
    int left = (int)m->wx - 7;
    return (int)x >= left;
}

static uint8_t ppu_background_color(const gbb_instance *m, unsigned x) {
    int window = (m->lcdc & 0x01u) != 0 && ppu_window_visible_at(m, x);
    unsigned source_x;
    unsigned source_y;
    uint16_t map_base;
    if (window) {
        source_x = (unsigned)((int)x - ((int)m->wx - 7));
        source_y = m->ppu_window_line;
        map_base = (m->lcdc & 0x40u) != 0 ? 0x1C00u : 0x1800u;
    } else {
        source_x = (uint8_t)(x + m->scx);
        source_y = (uint8_t)(m->ly + m->scy);
        map_base = (m->lcdc & 0x08u) != 0 ? 0x1C00u : 0x1800u;
    }
    uint16_t map_index = (uint16_t)(((source_y >> 3) * 32u) + ((source_x & 0xFFu) >> 3));
    uint16_t map_address = (uint16_t)(map_base + map_index);
    if (map_address >= sizeof(m->vram)) return 0;
    uint8_t tile = m->vram[map_address];
    return ppu_tile_color(m, tile, source_y & 7u, source_x & 7u, 0);
}

static void ppu_begin_object_scan(gbb_instance *m) {
    m->ppu_selected_object_count = 0;
    m->ppu_scan_index = 0;
}

/* Sample one OAM entry every two modeled mode-2 dots. If DMA overlaps that
 * read, this software model treats the candidate as off-screen for the line.
 * The scan-dot placement remains policy, not measured CPU-B timing. */
static void ppu_scan_object(gbb_instance *m, unsigned index) {
    if (index >= 40u) return;
    m->ppu_scan_index = (uint8_t)(index + 1u);
    /* Private observer access 9 marks the per-entry mode-2 sample; value 0
     * means DMA suppressed the candidate, value 1 means OAM was sampled. */
    if (m->ly == 0u)
        observe_ppu(m, (uint16_t)(0xFE00u + index), 9,
                    (uint8_t)(m->dma_active ? 0u : 1u));
    if (m->dma_active || m->ppu_selected_object_count >= GBB_LINE_OBJECT_LIMIT)
        return;
    unsigned height = (m->lcdc & 0x04u) != 0 ? 16u : 8u;
    unsigned offset = index * 4u;
    uint8_t y = m->oam[offset];
    int top = (int)y - 16;
    if ((int)m->ly < top || (int)m->ly >= top + (int)height) return;
    uint8_t slot = m->ppu_selected_object_count++;
    m->ppu_selected_objects[slot] = (uint8_t)index;
    m->ppu_selected_y[slot] = y;
    m->ppu_selected_x[slot] = m->oam[offset + 1u];
    m->ppu_selected_tile[slot] = m->oam[offset + 2u];
    m->ppu_selected_attributes[slot] = m->oam[offset + 3u];
}

static int ppu_object_color(const gbb_instance *m, unsigned x, uint8_t *color,
                            uint8_t *attributes) {
    if ((m->lcdc & 0x02u) == 0) return 0;
    int found = 0;
    int best_left = 0;
    unsigned best_index = 0;
    uint8_t best_color = 0;
    uint8_t best_attributes = 0;
    unsigned height = (m->lcdc & 0x04u) != 0 ? 16u : 8u;
    for (unsigned selected = 0; selected < m->ppu_selected_object_count; ++selected) {
        unsigned index = m->ppu_selected_objects[selected];
        int left = (int)m->ppu_selected_x[selected] - 8;
        int local_x = (int)x - left;
        if (local_x < 0 || local_x >= 8) continue;
        int row = (int)m->ly - ((int)m->ppu_selected_y[selected] - 16);
        if (row < 0 || row >= (int)height) continue;
        uint8_t attributes = m->ppu_selected_attributes[selected];
        if ((attributes & 0x40u) != 0) row = (int)height - 1 - row;
        unsigned tile = m->ppu_selected_tile[selected];
        if (height == 16u) {
            tile &= ~1u;
            tile += (unsigned)row >> 3;
        }
        unsigned source_x = (attributes & 0x20u) != 0
            ? 7u - (unsigned)local_x : (unsigned)local_x;
        uint8_t candidate = ppu_tile_color(m, (uint8_t)tile,
                                           (unsigned)row & 7u, source_x, 1);
        if (candidate == 0) continue; /* OBJ color 0 is transparent before palette lookup. */
        if (!found || left < best_left || (left == best_left && index < best_index)) {
            found = 1;
            best_left = left;
            best_index = index;
            best_color = candidate;
            best_attributes = attributes;
        }
    }
    if (!found) return 0;
    *color = best_color;
    *attributes = best_attributes;
    return 1;
}

static uint8_t ppu_palette_shade(uint8_t palette, uint8_t color) {
    return (uint8_t)((palette >> (color * 2u)) & 3u);
}

static uint8_t ppu_pixel_shade(gbb_instance *m, unsigned x) {
    uint8_t background = (m->lcdc & 0x01u) != 0 ? ppu_background_color(m, x) : 0;
    if ((m->lcdc & 0x01u) != 0 && ppu_window_visible_at(m, x))
        m->ppu_window_line_drawn = 1;
    uint8_t object = 0, attributes = 0;
    if (ppu_object_color(m, x, &object, &attributes) &&
        ((attributes & 0x80u) == 0 || background == 0)) {
        uint8_t palette = (attributes & 0x10u) != 0 ? m->obp1 : m->obp0;
        return ppu_palette_shade(palette, object);
    }
    return ppu_palette_shade(m->bgp, background);
}

static void ppu_begin_transfer(gbb_instance *m) {
    m->ppu_fifo_head = 0;
    m->ppu_fifo_count = 0;
    m->ppu_fetch_stage = 0;
    m->ppu_fetch_phase = 0;
    m->ppu_fetch_enqueued = 0;
    m->ppu_transfer_age = 0;
    m->ppu_output_x = 0;
    m->ppu_fine_scroll = (uint8_t)(m->scx & 7u);
    m->ppu_scroll_discard = m->ppu_fine_scroll;
    m->ppu_mode3_stall = 0;
    m->ppu_window_started = 0;
    m->ppu_transfer_complete = 0;
    m->ppu_objects_stalled = 0;
    m->ppu_object_tiles_fetched = 0;
}

static void ppu_fetcher_step(gbb_instance *m) {
    uint16_t needed = (uint16_t)(GBB_FRAME_WIDTH + m->ppu_fine_scroll);
    if (m->ppu_fetch_enqueued >= needed) return;
    if (m->ppu_fetch_stage == 3u && m->ppu_fetch_phase == 1u) {
        if (m->ppu_fifo_count > 8u) return;
        uint16_t remaining = (uint16_t)(needed - m->ppu_fetch_enqueued);
        uint8_t push_count = (uint8_t)(remaining < 8u ? remaining : 8u);
        for (uint8_t i = 0; i < push_count; ++i) {
            uint8_t tail = (uint8_t)((m->ppu_fifo_head + m->ppu_fifo_count) %
                                     GBB_PPU_FIFO_CAPACITY);
            /* Queue bounded screen-pixel slots; shading stays in the common compositor. */
            m->ppu_fifo[tail] = m->ppu_fetch_enqueued < m->ppu_fine_scroll
                ? UINT8_MAX
                : (uint8_t)(m->ppu_fetch_enqueued - m->ppu_fine_scroll);
            ++m->ppu_fifo_count;
            ++m->ppu_fetch_enqueued;
        }
        m->ppu_fetch_phase = 0;
        m->ppu_fetch_stage = 0;
        return;
    }
    if (++m->ppu_fetch_phase == 2u) {
        m->ppu_fetch_phase = 0;
        m->ppu_fetch_stage = (uint8_t)((m->ppu_fetch_stage + 1u) & 3u);
    }
}

static int ppu_window_should_start(const gbb_instance *m) {
    if (m->ppu_window_started || (m->lcdc & 0x21u) != 0x21u ||
        m->ly < m->wy || m->wx > 166u) return 0;
    unsigned start_x = m->wx < 7u ? 0u : (unsigned)m->wx - 7u;
    return m->ppu_output_x == start_x;
}

static int ppu_object_should_stall(gbb_instance *m, uint8_t *stall) {
    if ((m->lcdc & 0x02u) == 0) return 0;
    unsigned fine_scroll = m->ppu_fine_scroll;
    for (uint8_t i = 0; i < m->ppu_selected_object_count; ++i) {
        uint16_t object_bit = (uint16_t)(1u << i);
        if ((m->ppu_objects_stalled & object_bit) != 0) continue;
        unsigned offset = (unsigned)m->ppu_selected_objects[i] * 4u;
        int left = (int)m->ppu_selected_x[i] - 8;
        /* X=0 is wholly offscreen; negative starts are outside this timing claim. */
        if (left < 0 || left >= (int)GBB_FRAME_WIDTH ||
            left != (int)m->ppu_output_x) continue;
        m->ppu_objects_stalled |= object_bit;
        if (m->dma_active) {
            /* advance_devices_to advances the DMA byte before this PPU event.
             * The aligned word read is the declared deterministic model; its
             * CPU-B lane and tie timing remain unmeasured. */
            unsigned word = (unsigned)m->dma_index & ~1u;
            if (word + 1u < GBB_OAM_BYTES) {
                m->ppu_selected_tile[i] = m->oam[word];
                m->ppu_selected_attributes[i] = m->oam[word + 1u];
            }
        } else {
            m->ppu_selected_tile[i] = m->oam[offset + 2u];
            m->ppu_selected_attributes[i] = m->oam[offset + 3u];
        }
        /* Private test observer: access 8 marks the selected-object fetch
         * boundary and records its latched tile. It is not part of the public
         * emulator API or guest-visible state. */
        if (m->ly == 0u)
            observe_ppu(m, (uint16_t)(0xFE00u + m->ppu_selected_objects[i]), 8,
                        m->ppu_selected_tile[i]);
        unsigned tile = ((unsigned)left + fine_scroll) >> 3;
        uint32_t tile_bit = tile < 32u ? (UINT32_C(1) << tile) : 0;
        if (tile_bit != 0 && (m->ppu_object_tiles_fetched & tile_bit) != 0) {
            *stall = 6u;
        } else {
            unsigned fetch_offset = ((unsigned)left + fine_scroll) & 7u;
            if (fetch_offset > 5u) fetch_offset = 5u;
            *stall = (uint8_t)(11u - fetch_offset);
            m->ppu_object_tiles_fetched |= tile_bit;
        }
        return 1;
    }
    return 0;
}

static void ppu_transfer_dot(gbb_instance *m) {
    if (m->ppu_transfer_complete) {
        ppu_set_mode(m, 0);
        return;
    }
    ppu_fetcher_step(m);
    if (m->ppu_transfer_age < 12u) {
        ++m->ppu_transfer_age;
        if (m->ppu_transfer_age < 12u) return;
    }
    if (m->ppu_mode3_stall != 0) {
        --m->ppu_mode3_stall;
        return;
    }
    if (m->ppu_fifo_count == 0) return;

    uint8_t fetched_slot = m->ppu_fifo[m->ppu_fifo_head];
    if (fetched_slot == UINT8_MAX && m->ppu_scroll_discard != 0) {
        m->ppu_fifo_head = (uint8_t)((m->ppu_fifo_head + 1u) % GBB_PPU_FIFO_CAPACITY);
        --m->ppu_fifo_count;
        --m->ppu_scroll_discard;
        return;
    }
    if (fetched_slot >= GBB_FRAME_WIDTH || fetched_slot != m->ppu_output_x) {
        m->ppu_transfer_complete = 1;
        return;
    }
    if (ppu_window_should_start(m)) {
        m->ppu_window_started = 1;
        m->ppu_mode3_stall = (uint8_t)(m->wx == 0u && (m->scx & 7u) != 0 ? 5u : 6u);
        --m->ppu_mode3_stall;
        return;
    }
    uint8_t object_stall = 0;
    if (ppu_object_should_stall(m, &object_stall)) {
        m->ppu_mode3_stall = object_stall;
        --m->ppu_mode3_stall;
        return;
    }

    m->ppu_fifo_head = (uint8_t)((m->ppu_fifo_head + 1u) % GBB_PPU_FIFO_CAPACITY);
    --m->ppu_fifo_count;
    m->frame_working[(unsigned)m->ly * GBB_FRAME_WIDTH + fetched_slot] =
        ppu_pixel_shade(m, fetched_slot);
    if (++m->ppu_output_x == GBB_FRAME_WIDTH) m->ppu_transfer_complete = 1;
}

static void ppu_advance_dot(gbb_instance *m) {
    if ((m->lcdc & 0x80u) == 0) return;
    if (m->ppu_dot < 455u) {
        ++m->ppu_dot;
    } else {
        if (m->ly < GBB_FRAME_HEIGHT && m->ppu_window_line_drawn &&
            m->ppu_window_line != UINT8_MAX)
            ++m->ppu_window_line;
        m->ppu_dot = 0;
        ++m->ly;
        if (m->ly == 154u) {
            m->ly = 0;
            m->ppu_window_line = 0;
        }
        observe_ppu(m, 0xFF44, 6, m->ly);
        m->ppu_window_line_drawn = 0;
        m->ppu_transfer_complete = 0;
        if (m->ly < GBB_FRAME_HEIGHT) ppu_begin_object_scan(m);
        if (m->ly == GBB_FRAME_HEIGHT) {
            memcpy(m->frame_completed, m->frame_working, sizeof(m->frame_completed));
            if (m->frame_generation != UINT64_MAX) ++m->frame_generation;
            m->frame_completion_half_dots = m->time_half_dots;
            m->interrupt_flags |= 0x01u;
            observe_ppu(m, 0xFF0F, 7, (uint8_t)(0xE0u | m->interrupt_flags));
        }
        ppu_set_mode(m, m->ly >= GBB_FRAME_HEIGHT ? 1u : 2u);
        ppu_update_stat_line(m);
    }
    if (m->ly >= GBB_FRAME_HEIGHT) {
        ppu_set_mode(m, 1);
    } else if (m->ppu_dot < 80u) {
        ppu_set_mode(m, 2);
        if ((m->ppu_dot & 1u) == 0u)
            ppu_scan_object(m, (unsigned)(m->ppu_dot / 2u) - 1u);
    } else if (m->ppu_dot == 80u) {
        ppu_begin_transfer(m);
        ppu_set_mode(m, 3);
    } else if (m->ppu_mode == 3u) {
        ppu_transfer_dot(m);
    }
}

static uint8_t dma_source_read(const gbb_instance *m, uint16_t address) {
    if (address >= 0x8000u && address <= 0x9FFFu)
        return m->vram[address - 0x8000u];
    if (address >= 0xC000u && address <= 0xDFFFu)
        return m->wram[address - 0xC000u];
    /* The ROM-only profile has no external cartridge RAM. Other source pages
     * are outside the DMG manual's 8000-DFFF DMA range. */
    return 0xFFu;
}

static void dma_start(gbb_instance *m) {
    m->dma_page = m->dma_pending_page;
    m->dma_index = 0;
    m->dma_phase = 0;
    m->dma_active = 1;
    m->dma_cpu_blocked = 0;
    m->dma_start_pending = 0;
    observe_dma(m, 0xFF46u, 1, m->dma_page);
}

static void dma_advance_half_dot(gbb_instance *m) {
    if (!m->dma_active) return;
    if (++m->dma_phase < GBB_DMA_BYTE_PERIOD_HALF_DOTS) return;
    m->dma_phase = 0;
    m->dma_cpu_blocked = 1;
    uint16_t source = (uint16_t)(((uint16_t)m->dma_page << 8) | m->dma_index);
    uint8_t value = dma_source_read(m, source);
    m->oam[m->dma_index] = value;
    observe_dma(m, (uint16_t)(0xFE00u + m->dma_index), 2, value);
    ++m->dma_index;
    if (m->dma_index == GBB_OAM_BYTES) {
        m->dma_active = 0;
        observe_dma(m, 0xFF46u, 3, m->dma_page);
    }
}

static void advance_devices_to(gbb_instance *m, uint64_t target) {
    while (m->time_half_dots < target) {
        ++m->time_half_dots;
        apply_input_events_now(m);
        if (m->timer_reload_pending && m->timer_reload_remaining != 0 &&
            --m->timer_reload_remaining == 0) {
            m->tima = m->tma;
            m->timer_reload_pending = 0;
            m->timer_reloaded_at = m->time_half_dots;
            m->interrupt_flags |= 0x04u;
            observe_bus(m, 0, 0xFF05, 3, m->tima);
            observe_bus(m, 0, 0xFF0F, 3, (uint8_t)(0xE0u | m->interrupt_flags));
            diagnostic_add(m, GBB_DIAGNOSTIC_TIMER, m->time_half_dots, 0xFF05, m->tima);
        }
        if (m->serial_active && (m->serial_control & 1u) != 0 &&
            m->serial_edge_remaining != 0 && --m->serial_edge_remaining == 0) {
            m->serial_data = (uint8_t)((m->serial_data << 1) | 1u);
            if (++m->serial_bits == 8u) {
                m->serial_active = 0;
                m->serial_control &= 1u;
                m->interrupt_flags |= 0x08u;
            } else {
                m->serial_edge_remaining = 1024u;
            }
        }
        m->divider_phase ^= 1u;
        if (m->divider_phase == 0) {
            ++m->divider_counter;
            m->div = (uint8_t)(m->divider_counter >> 8);
            timer_set_signal(m, timer_input(m), m->time_half_dots);
        }
        dma_advance_half_dot(m);
        m->ppu_half_phase ^= 1u;
        if (m->ppu_half_phase == 0) ppu_advance_dot(m);
    }
}

gbb_error gbb_queue_events(gbb_instance *instance, const gbb_input_event *events,
                           size_t count) {
    if (instance == NULL || (events == NULL && count != 0)) return GBB_INVALID_ARGUMENT;
    if (count == 0) return GBB_OK;
    if (count > GBB_INPUT_EVENT_CAPACITY - instance->input_event_count)
        return GBB_EVENT_QUEUE_FULL;
    uint64_t previous = instance->time_half_dots;
    if (instance->input_event_count != 0)
        previous = instance->input_events[instance->input_event_count - 1].at_half_dots;
    for (size_t i = 0; i < count; ++i) {
        const gbb_input_event *event = &events[i];
        if (event->at_half_dots < instance->time_half_dots || event->at_half_dots < previous)
            return GBB_INVALID_EVENT;
        if ((event->kind == GBB_INPUT_STOP_WAKE && event->value != 1u) ||
            (event->kind == GBB_INPUT_SERIAL_EDGE && event->value > 1u) ||
            ((event->kind == GBB_INPUT_BUTTON_PRESS || event->kind == GBB_INPUT_BUTTON_RELEASE) &&
             event->value > GBB_BUTTON_START) ||
            (event->kind != GBB_INPUT_STOP_WAKE && event->kind != GBB_INPUT_SERIAL_EDGE &&
             event->kind != GBB_INPUT_BUTTON_PRESS && event->kind != GBB_INPUT_BUTTON_RELEASE))
            return GBB_INVALID_EVENT;
        previous = event->at_half_dots;
    }
    memcpy(instance->input_events + instance->input_event_count, events,
           count * sizeof(*events));
    instance->input_event_count += count;
    return GBB_OK;
}

gbb_error gbb_copy_frame(const gbb_instance *instance, uint8_t *pixels,
                         size_t capacity_bytes, size_t pitch_bytes,
                         gbb_frame_info *out_info) {
    if (instance == NULL || pixels == NULL || out_info == NULL) return GBB_INVALID_ARGUMENT;
    if (pitch_bytes < GBB_FRAME_WIDTH ||
        pitch_bytes > (SIZE_MAX - GBB_FRAME_WIDTH) / (GBB_FRAME_HEIGHT - 1u))
        return GBB_INVALID_ARGUMENT;
    size_t required = (GBB_FRAME_HEIGHT - 1u) * pitch_bytes + GBB_FRAME_WIDTH;
    if (capacity_bytes < required) return GBB_INVALID_ARGUMENT;

    uintptr_t pixels_begin = (uintptr_t)(void *)pixels;
    uintptr_t info_begin = (uintptr_t)(void *)out_info;
    if (capacity_bytes > UINTPTR_MAX - pixels_begin ||
        sizeof(*out_info) > UINTPTR_MAX - info_begin)
        return GBB_INVALID_ARGUMENT;
    uintptr_t pixels_end = pixels_begin + capacity_bytes;
    uintptr_t info_end = info_begin + sizeof(*out_info);
    if (pixels_begin < info_end && info_begin < pixels_end)
        return GBB_INVALID_ARGUMENT;
    if (instance->frame_generation == 0) return GBB_FRAME_NOT_READY;
    for (size_t y = 0; y < GBB_FRAME_HEIGHT; ++y)
        memcpy(pixels + y * pitch_bytes,
               instance->frame_completed + y * GBB_FRAME_WIDTH, GBB_FRAME_WIDTH);
    gbb_frame_info info = {GBB_FRAME_WIDTH, GBB_FRAME_HEIGHT,
                           instance->frame_generation,
                           instance->frame_completion_half_dots};
    *out_info = info;
    return GBB_OK;
}

static void advance_devices(gbb_instance *m, uint64_t half_dots) {
    advance_devices_to(m, m->time_half_dots + half_dots);
}
static void set_hl(gbb_instance *m, uint16_t value) { m->h = (uint8_t)(value >> 8); m->l = (uint8_t)value; }

static gbb_error validate_header(const uint8_t *rom, size_t size) {
    if (rom == NULL || size == 0) return GBB_INVALID_ARGUMENT;
    if (size < 0x150) return GBB_ROM_TRUNCATED;
    if (size > GBB_MAX_ROM_SIZE) return GBB_ROM_TOO_LARGE;
    if (rom[0x147] != 0) return GBB_UNSUPPORTED_CARTRIDGE;
    if (rom[0x148] > 0) return GBB_UNSUPPORTED_ROM_SIZE;
    if (rom[0x149] != 0) return GBB_UNSUPPORTED_RAM_SIZE;
    size_t declared = 32768u << rom[0x148];
    if (size < declared) return GBB_ROM_TRUNCATED;
    if (size != declared) return GBB_ROM_SIZE_MISMATCH;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    return checksum == rom[0x14D] ? GBB_OK : GBB_INVALID_ROM;
}

gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance) {
    if (out_instance == NULL) return GBB_INVALID_ARGUMENT;
    *out_instance = NULL;
    if (profile != GBB_PROFILE_DMG_CPU_B) return GBB_UNSUPPORTED_PROFILE;
    gbb_instance *m = calloc(1, sizeof(*m));
    if (m == NULL) return GBB_OUT_OF_MEMORY;
    reset_state(m); /* RAM fill is emulator policy; hardware power-on RAM is unspecified. */
    *out_instance = m;
    return GBB_OK;
}

void gbb_destroy(gbb_instance *instance) {
    if (instance != NULL) { free(instance->rom); free(instance); }
}

gbb_error gbb_reset(gbb_instance *instance) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    reset_state(instance);
    return GBB_OK;
}

gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    gbb_error validation = validate_header(rom, rom_size);
    if (validation != GBB_OK) return validation;
    uint8_t *copy = malloc(rom_size);
    if (copy == NULL) return GBB_OUT_OF_MEMORY;
    memcpy(copy, rom, rom_size);
    free(instance->rom);
    instance->rom = copy;
    instance->rom_size = rom_size;
    reset_state(instance);
    instance->loaded = 1;
    return GBB_OK;
}

typedef struct { uint8_t size; uint8_t ticks; int supported; } decoded;

static int is_unused_opcode(uint8_t op) {
    return op == 0xD3 || op == 0xDB || op == 0xDD || op == 0xE3 || op == 0xE4 ||
           op == 0xEB || op == 0xEC || op == 0xED || op == 0xF4 || op == 0xFC || op == 0xFD;
}

static int condition_true(const gbb_instance *m, unsigned condition) {
    switch (condition & 3u) {
        case 0: return (m->f & 0x80) == 0;
        case 1: return (m->f & 0x80) != 0;
        case 2: return (m->f & 0x10) == 0;
        default: return (m->f & 0x10) != 0;
    }
}

static decoded decode(const gbb_instance *m) {
    uint8_t op = read8(m, m->pc);
    if (is_unused_opcode(op)) return (decoded){1, 0, 0};
    if (op == 0xCB) {
        uint8_t extension = instruction_byte(m, m->pc, 1);
        unsigned group = extension >> 6;
        unsigned target = extension & 7u;
        uint8_t ticks = target == 6u ? (uint8_t)(group == 1u ? 24u : 32u) : 16u;
        return (decoded){2, ticks, 1};
    }
    if ((op & 0xC7u) == 0x06u) return (decoded){2, (uint8_t)(((op >> 3) & 7u) == 6u ? 24 : 16), 1};
    if ((op & 0xCFu) == 0x01u) return (decoded){3, 24, 1};
    if ((op & 0xCFu) == 0x03u || (op & 0xCFu) == 0x0Bu || (op & 0xCFu) == 0x09u) return (decoded){1, 16, 1};
    if ((op & 0xC7u) == 0x04u || (op & 0xC7u) == 0x05u) return (decoded){1, (uint8_t)(((op >> 3) & 7u) == 6u ? 24 : 8), 1};
    if (op >= 0x40 && op <= 0x7F) return (decoded){1, (uint8_t)((op == 0x76 || ((op & 7u) != 6u && ((op >> 3) & 7u) != 6u)) ? 8 : 16), 1};
    if (op >= 0x80 && op <= 0xBF) return (decoded){1, (uint8_t)((op & 7u) == 6u ? 16 : 8), 1};
    if ((op & 0xE7u) == 0x20u) return (decoded){2, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 24 : 16), 1};
    if ((op & 0xE7u) == 0xC0u) return (decoded){1, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 40 : 16), 1};
    if ((op & 0xE7u) == 0xC2u) return (decoded){3, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 32 : 24), 1};
    if ((op & 0xE7u) == 0xC4u) return (decoded){3, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 48 : 24), 1};
    if ((op & 0xCFu) == 0xC1u) return (decoded){1, (uint8_t)(op == 0xF1 ? 24 : 24), 1};
    if ((op & 0xCFu) == 0xC5u) return (decoded){1, 32, 1};
    if ((op & 0xC7u) == 0xC6u) return (decoded){2, 16, 1};
    if ((op & 0xC7u) == 0xC7u) return (decoded){1, 32, 1};
    switch (op) {
        case 0x00: case 0x07: case 0x0F: case 0x10: case 0x17: case 0x1F:
        case 0x27: case 0x2F: case 0x37: case 0x3F: case 0x76: case 0xC9:
        case 0xD9: case 0xE9: case 0xF3: case 0xFB:
            return (decoded){(uint8_t)(op == 0x10 ? 2 : 1), (uint8_t)((op == 0xC9 || op == 0xD9) ? 32 : 8), 1};
        case 0x08: return (decoded){3, 40, 1};
        case 0x18: return (decoded){2, 24, 1};
        case 0x02: case 0x0A: case 0x12: case 0x1A:
        case 0x22: case 0x2A: case 0x32: case 0x3A: return (decoded){1, 16, 1};
        case 0xC3: return (decoded){3, 32, 1};
        case 0xCD: return (decoded){3, 48, 1};
        case 0xE0: case 0xF0: return (decoded){2, 24, 1};
        case 0xE2: case 0xF2: return (decoded){1, 16, 1};
        case 0xE8: return (decoded){2, 48, 1};
        case 0xEA: case 0xFA: return (decoded){3, 32, 1};
        case 0xF8: return (decoded){2, 24, 1};
        case 0xF9: return (decoded){1, 16, 1};
        default: return (decoded){1, 8, 1};
    }
}

static uint8_t instruction_cost(const gbb_instance *m, decoded d) { (void)m; return d.ticks; }

static uint16_t pair_value(const gbb_instance *m, unsigned pair) {
    switch (pair & 3u) {
        case 0: return (uint16_t)(((uint16_t)m->b << 8) | m->c);
        case 1: return (uint16_t)(((uint16_t)m->d << 8) | m->e);
        case 2: return hl(m);
        default: return m->sp;
    }
}

static int instruction_reads_supported(const gbb_instance *m, decoded d, uint8_t op) {
    /* Address checks have no bus phases or side effects. Every byte is checked
     * before an instruction can change registers, RAM, devices or outputs. */
    for (unsigned i = 0; i < d.size; ++i)
        if (!read_supported(instruction_address(m, m->pc, i))) return 0;

    if (op == 0xCB)
        return (instruction_byte(m, m->pc, 1) & 7u) != 6u || read_supported(hl(m));
    if ((op >= 0x40 && op <= 0x7F && op != 0x76 && (op & 7u) == 6u) ||
        (op >= 0x80 && op <= 0xBF && (op & 7u) == 6u) ||
        (((op & 0xC7u) == 0x04u || (op & 0xC7u) == 0x05u) && ((op >> 3) & 7u) == 6u) ||
        op == 0x2A || op == 0x3A)
        return read_supported(hl(m));

    if ((op & 0xCFu) == 0xC1u || op == 0xC9 || op == 0xD9 ||
        ((op & 0xE7u) == 0xC0u && condition_true(m, (op >> 3) & 3u)))
        return read_supported(m->sp) && read_supported((uint16_t)(m->sp + 1u));

    switch (op) {
        case 0x0A: return read_supported(pair_value(m, 0));
        case 0x1A: return read_supported(pair_value(m, 1));
        case 0xF0: return read_supported((uint16_t)(0xFF00u + instruction_byte(m, m->pc, 1)));
        case 0xF2: return read_supported((uint16_t)(0xFF00u + m->c));
        case 0xFA: {
            uint16_t address = (uint16_t)(instruction_byte(m, m->pc, 1) |
                               ((uint16_t)instruction_byte(m, m->pc, 2) << 8));
            return read_supported(address);
        }
        default: return 1; /* Writes to absent ROM-only regions remain ignored. */
    }
}

static void set_pair(gbb_instance *m, unsigned pair, uint16_t value) {
    switch (pair & 3u) {
        case 0: m->b=(uint8_t)(value>>8); m->c=(uint8_t)value; break;
        case 1: m->d=(uint8_t)(value>>8); m->e=(uint8_t)value; break;
        case 2: set_hl(m,value); break;
        default: m->sp=value; break;
    }
}

static uint16_t stack_pair(const gbb_instance *m, unsigned pair) {
    return pair == 3 ? (uint16_t)(((uint16_t)m->a << 8) | m->f) : pair_value(m,pair);
}

static void set_stack_pair(gbb_instance *m, unsigned pair, uint16_t value) {
    if (pair == 3) { m->a=(uint8_t)(value>>8); m->f=(uint8_t)(value&0xF0u); }
    else set_pair(m,pair,value);
}

static uint8_t get_reg(gbb_instance *m, unsigned reg, uint64_t offset) {
    switch (reg & 7u) {
        case 0: return m->b; case 1: return m->c; case 2: return m->d; case 3: return m->e;
        case 4: return m->h; case 5: return m->l; case 6: return bus_read(m,hl(m),offset); default: return m->a;
    }
}

static void set_reg(gbb_instance *m, unsigned reg, uint8_t value, uint64_t offset) {
    switch (reg & 7u) {
        case 0: m->b=value; break; case 1: m->c=value; break; case 2: m->d=value; break; case 3: m->e=value; break;
        case 4: m->h=value; break; case 5: m->l=value; break; case 6: bus_write(m,hl(m),value,offset); break; default: m->a=value; break;
    }
}

static void execute_cb(gbb_instance *m, uint16_t pc, uint8_t extension) {
    unsigned group = extension >> 6;
    unsigned operation = (extension >> 3) & 7u;
    unsigned target = extension & 7u;
    uint8_t value = get_reg(m, target, 16);
    if (group == 0u) {
        uint8_t carry_in = (uint8_t)((m->f & 0x10u) != 0);
        uint8_t carry_out = 0;
        switch (operation) {
            case 0: carry_out = (uint8_t)(value >> 7); value = (uint8_t)((value << 1) | carry_out); break;
            case 1: carry_out = (uint8_t)(value & 1u); value = (uint8_t)((value >> 1) | (carry_out << 7)); break;
            case 2: { uint8_t out = (uint8_t)(value >> 7); value = (uint8_t)((value << 1) | carry_in); carry_out = out; break; }
            case 3: { uint8_t out = (uint8_t)(value & 1u); value = (uint8_t)((value >> 1) | (carry_in << 7)); carry_out = out; break; }
            case 4: carry_out = (uint8_t)(value >> 7); value = (uint8_t)(value << 1); break;
            case 5: carry_out = (uint8_t)(value & 1u); value = (uint8_t)((value >> 1) | (value & 0x80u)); break;
            case 6: value = (uint8_t)((value << 4) | (value >> 4)); break;
            default: carry_out = (uint8_t)(value & 1u); value = (uint8_t)(value >> 1); break;
        }
        m->f = (uint8_t)((value == 0 ? 0x80u : 0u) | (carry_out ? 0x10u : 0u));
        set_reg(m, target, value, 24);
    } else if (group == 1u) {
        unsigned bit = operation;
        uint8_t carry = (uint8_t)(m->f & 0x10u);
        m->f = (uint8_t)(carry | 0x20u | ((value & (uint8_t)(1u << bit)) == 0 ? 0x80u : 0));
    } else if (group == 2u) {
        value = (uint8_t)(value & (uint8_t)~(1u << operation));
        set_reg(m, target, value, 24);
    } else {
        value = (uint8_t)(value | (uint8_t)(1u << operation));
        set_reg(m, target, value, 24);
    }
    m->pc = (uint16_t)(pc + 2u);
}

static uint8_t add8(gbb_instance *m, uint8_t lhs, uint8_t rhs, unsigned carry) {
    unsigned sum=(unsigned)lhs+(unsigned)rhs+carry; uint8_t result=(uint8_t)sum;
    m->f=(uint8_t)((result==0?0x80:0)|(((lhs&15u)+(rhs&15u)+carry>15u)?0x20:0)|(sum>255u?0x10:0)); return result;
}

static uint8_t sub8(gbb_instance *m, uint8_t lhs, uint8_t rhs, unsigned carry) {
    unsigned sub=(unsigned)rhs+carry; uint8_t result=(uint8_t)((unsigned)lhs-sub);
    m->f=(uint8_t)(0x40|(result==0?0x80:0)|((lhs&15u)<((rhs&15u)+carry)?0x20:0)|((unsigned)lhs<sub?0x10:0)); return result;
}

static void alu(gbb_instance *m, unsigned operation, uint8_t value) {
    switch (operation & 7u) {
        case 0: m->a=add8(m,m->a,value,0); break;
        case 1: m->a=add8(m,m->a,value,(m->f&0x10u)!=0); break;
        case 2: m->a=sub8(m,m->a,value,0); break;
        case 3: m->a=sub8(m,m->a,value,(m->f&0x10u)!=0); break;
        case 4: m->a&=value; m->f=(uint8_t)((m->a==0?0x80:0)|0x20); break;
        case 5: m->a^=value; m->f=(uint8_t)(m->a==0?0x80:0); break;
        case 6: m->a|=value; m->f=(uint8_t)(m->a==0?0x80:0); break;
        default: (void)sub8(m,m->a,value,0); break;
    }
}

static void push16(gbb_instance *m, uint16_t value, uint64_t high_time, uint64_t low_time) {
    --m->sp; bus_write(m,m->sp,(uint8_t)(value>>8),high_time);
    --m->sp; bus_write(m,m->sp,(uint8_t)value,low_time);
}

static uint16_t pop16(gbb_instance *m, uint64_t low_time, uint64_t high_time) {
    uint8_t lo=bus_read(m,m->sp,low_time); ++m->sp;
    uint8_t hi=bus_read(m,m->sp,high_time); ++m->sp;
    return (uint16_t)(lo | ((uint16_t)hi<<8));
}

static void execute(gbb_instance *m, uint8_t cost) {
    uint16_t pc=m->pc; uint8_t op=read8(m,pc); uint64_t base=0;
    if (op>=0x40 && op<=0x7F) {
        if (op==0x76) {
            if (!m->ime && pending_interrupt(m) < 5) m->halt_bug=1;
            else m->halted=1;
            m->pc=(uint16_t)(pc+1);
        }
        else { uint8_t value=get_reg(m,op&7u,8); set_reg(m,(op>>3)&7u,value,16); m->pc=(uint16_t)(pc+1); }
    } else if (op>=0x80 && op<=0xBF) {
        uint8_t value=get_reg(m,op&7u,8); alu(m,(op>>3)&7u,value); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xC7u)==0x04u || (op&0xC7u)==0x05u) {
        unsigned reg=(op>>3)&7u; uint8_t old=get_reg(m,reg,8); uint8_t carry=(uint8_t)(m->f&0x10u);
        uint8_t value=(op&1u)?(uint8_t)(old-1u):(uint8_t)(old+1u);
        if (op&1u) m->f=(uint8_t)(carry|0x40u|(value==0?0x80:0)|((old&15u)==0?0x20:0));
        else m->f=(uint8_t)(carry|(value==0?0x80:0)|((old&15u)==15u?0x20:0));
        set_reg(m,reg,value,16); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xC7u)==0x06u) {
        uint8_t value=instruction_byte(m,pc,1); set_reg(m,(op>>3)&7u,value,16); m->pc=(uint16_t)(pc+2);
    } else if ((op&0xCFu)==0x01u) {
        uint16_t value=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8)); set_pair(m,(op>>4)&3u,value); m->pc=(uint16_t)(pc+3);
    } else if ((op&0xCFu)==0x03u || (op&0xCFu)==0x0Bu) {
        unsigned pair=(op>>4)&3u; uint16_t value=pair_value(m,pair); set_pair(m,pair,(uint16_t)(value+((op&8u)?-1:1))); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xCFu)==0x09u) {
        uint16_t lhs=hl(m), rhs=pair_value(m,(op>>4)&3u); uint32_t sum=(uint32_t)lhs+rhs;
        m->f=(uint8_t)((m->f&0x80u)|(((lhs&0xFFFu)+(rhs&0xFFFu)>0xFFFu)?0x20u:0)|(sum>0xFFFFu?0x10u:0)); set_hl(m,(uint16_t)sum); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xE7u)==0x20u) {
        int8_t offset=(int8_t)instruction_byte(m,pc,1); m->pc=(uint16_t)(pc+2); if(condition_true(m,(op>>3)&3u)) m->pc=(uint16_t)(m->pc+offset);
    } else if (op==0x18) { m->pc=(uint16_t)(pc+2+(int8_t)instruction_byte(m,pc,1)); }
    else if ((op&0xE7u)==0xC2u) { uint16_t dst=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8)); m->pc=condition_true(m,(op>>3)&3u)?dst:(uint16_t)(pc+3); }
    else if (op==0xC3) m->pc=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8));
    else if ((op&0xE7u)==0xC4u || op==0xCD) {
        uint16_t dst=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8)); int take=op==0xCD||condition_true(m,(op>>3)&3u);
        if(take){ push16(m,(uint16_t)(pc+3u-(m->halt_bug?1u:0u)),32,40); m->pc=dst; } else m->pc=(uint16_t)(pc+3);
    } else if ((op&0xE7u)==0xC0u || op==0xC9 || op==0xD9) {
        int take=op==0xC9||op==0xD9||condition_true(m,(op>>3)&3u);
        if(take){
            uint64_t low_phase = op == 0xC9 || op == 0xD9 ? 8u : 16u;
            m->pc=pop16(m,low_phase,low_phase+8u);
            if (op == 0xD9) { m->ime=1; m->ime_delay=0; }
        } else m->pc=(uint16_t)(pc+1);
    } else if ((op&0xCFu)==0xC1u) { set_stack_pair(m,(op>>4)&3u,pop16(m,8,16)); m->pc=(uint16_t)(pc+1); }
    else if ((op&0xCFu)==0xC5u) { push16(m,stack_pair(m,(op>>4)&3u),16,24); m->pc=(uint16_t)(pc+1); }
    else if ((op&0xC7u)==0xC6u) { uint8_t value=instruction_byte(m,pc,1); alu(m,(op>>3)&7u,value); m->pc=(uint16_t)(pc+2); }
    else if ((op&0xC7u)==0xC7u) { push16(m,(uint16_t)(pc+(m->halt_bug?0u:1u)),16,24); m->pc=(uint16_t)(op&0x38u); }
    else {
        switch(op) {
            case 0x00: m->pc++; break;
            case 0x02: bus_write(m,pair_value(m,0),m->a,8); m->pc++; break;
            case 0x0A: m->a=bus_read(m,pair_value(m,0),8); m->pc++; break;
            case 0x12: bus_write(m,pair_value(m,1),m->a,8); m->pc++; break;
            case 0x1A: m->a=bus_read(m,pair_value(m,1),8); m->pc++; break;
            case 0x22: bus_write(m,hl(m),m->a,8); set_hl(m,(uint16_t)(hl(m)+1)); m->pc++; break;
            case 0x2A: m->a=bus_read(m,hl(m),8); set_hl(m,(uint16_t)(hl(m)+1)); m->pc++; break;
            case 0x32: bus_write(m,hl(m),m->a,8); set_hl(m,(uint16_t)(hl(m)-1)); m->pc++; break;
            case 0x3A: m->a=bus_read(m,hl(m),8); set_hl(m,(uint16_t)(hl(m)-1)); m->pc++; break;
            case 0x08: { uint16_t addr=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8)); bus_write(m,addr,(uint8_t)m->sp,24); bus_write(m,(uint16_t)(addr+1),(uint8_t)(m->sp>>8),32); m->pc+=3; break; }
            case 0x10: m->pc=(uint16_t)(pc+2); m->stopped=1; break;
            case 0x07: { uint8_t c=(uint8_t)(m->a>>7); m->a=(uint8_t)((m->a<<1)|c); m->f=c?0x10:0; m->pc++; break; }
            case 0x0F: { uint8_t c=(uint8_t)(m->a&1); m->a=(uint8_t)((m->a>>1)|(c<<7)); m->f=c?0x10:0; m->pc++; break; }
            case 0x17: { uint8_t c=(uint8_t)(m->a>>7), old=(uint8_t)((m->f>>4)&1); m->a=(uint8_t)((m->a<<1)|old); m->f=c?0x10:0; m->pc++; break; }
            case 0x1F: { uint8_t c=(uint8_t)(m->a&1), old=(uint8_t)((m->f>>4)&1); m->a=(uint8_t)((m->a>>1)|(old<<7)); m->f=c?0x10:0; m->pc++; break; }
            case 0x27: { uint8_t correction=0; int carry=(m->f&0x10u)!=0; if((m->f&0x40u)==0){if((m->f&0x20u)||(m->a&15u)>9) correction|=6; if(carry||m->a>0x99){correction|=0x60;carry=1;} m->a=(uint8_t)(m->a+correction);}else{if(m->f&0x20u)correction|=6;if(carry)correction|=0x60;m->a=(uint8_t)(m->a-correction);} m->f=(uint8_t)((m->f&0x40u)|(m->a==0?0x80u:0)|(carry?0x10u:0));m->pc++;break; }
            case 0x2F: m->a=(uint8_t)~m->a; m->f=(uint8_t)((m->f&0x90u)|0x60u); m->pc++; break;
            case 0x37: m->f=(uint8_t)((m->f&0x80u)|0x10u); m->pc++; break;
            case 0x3F: m->f=(uint8_t)((m->f&0x80u)|((m->f&0x10u)?0:0x10u)); m->pc++; break;
            case 0xE0: bus_write(m,(uint16_t)(0xFF00u+instruction_byte(m,pc,1)),m->a,16); m->pc+=2; break;
            case 0xE2: bus_write(m,(uint16_t)(0xFF00u+m->c),m->a,8); m->pc++; break;
            case 0xF0: m->a=bus_read(m,(uint16_t)(0xFF00u+instruction_byte(m,pc,1)),16); m->pc+=2; break;
            case 0xF2: m->a=bus_read(m,(uint16_t)(0xFF00u+m->c),8); m->pc++; break;
            case 0xEA: { uint16_t addr=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8)); bus_write(m,addr,m->a,24); m->pc+=3; break; }
            case 0xFA: { uint16_t addr=(uint16_t)(instruction_byte(m,pc,1)|((uint16_t)instruction_byte(m,pc,2)<<8)); m->a=bus_read(m,addr,24); m->pc+=3; break; }
            case 0xE8: case 0xF8: { uint8_t e=instruction_byte(m,pc,1); uint16_t old=m->sp; uint16_t value=(uint16_t)(old+(int8_t)e); uint8_t flags=(uint8_t)(((old&15u)+(e&15u)>15u?0x20u:0)|((old&255u)+e>255u?0x10u:0)); if(op==0xE8)m->sp=value;else set_hl(m,value);m->f=flags;m->pc+=2;break; }
            case 0xF9: m->sp=hl(m); m->pc++; break;
            case 0xE9: m->pc=hl(m); break;
            case 0xF3: m->ime=0; m->ime_delay=0; m->pc++; break;
            case 0xFB: if (m->ime_delay == 0) m->ime_delay=2; m->pc++; break;
            case 0xCB: {
                uint8_t extension = instruction_byte(m, pc, 1);
                execute_cb(m, pc, extension);
                break;
            }
            default: m->pc=(uint16_t)(pc+1); break;
        }
    }
    m->f &= 0xF0u;
}

static unsigned pending_interrupt(const gbb_instance *m) {
    uint8_t pending = (uint8_t)(m->ie & m->interrupt_flags & 0x1Fu);
    for (unsigned bit = 0; bit < 5; ++bit) if (pending & (1u << bit)) return bit;
    return 5;
}

static void enter_interrupt(gbb_instance *m, unsigned bit) {
    uint8_t mask = (uint8_t)(1u << bit);
    m->ime = 0;
    m->ime_delay = 0;
    /* Device deadlines at the acknowledge phase precede the IF bus write. */
    advance_devices_to(m, m->instruction_start_half_dots + 8u);
    m->interrupt_flags = (uint8_t)(m->interrupt_flags & (uint8_t)~mask);
    observe_bus(m, 0, 0xFF0F, 2, (uint8_t)(0xE0u | m->interrupt_flags));
    push16(m, m->pc, 16, 24);
    m->pc = (uint16_t)(0x0040u + bit * 8u);
    m->halted = 0;
}

static void save_trace(const gbb_instance *m, decoded d, gbb_trace_record *r) {
    memset(r, 0, sizeof(*r));
    r->time_half_dots = m->time_half_dots; r->pc = m->pc; r->opcode_size = d.size;
    for (uint8_t i = 0; i < d.size && i < 3; ++i) r->opcode[i] = instruction_byte(m, m->pc, i);
    r->a=m->a; r->f=m->f; r->b=m->b; r->c=m->c; r->d=m->d; r->e=m->e; r->h=m->h; r->l=m->l; r->sp=m->sp;
}

/* Private regression seam, like the bus observer: no guest execution or reads. */
void gbb_test_cpu_snapshot(const gbb_instance *m, gbb_trace_record *record) {
    if (m != NULL && record != NULL) save_trace(m, (decoded){0, 0, 1}, record);
}

static int halt_bug_keeps_control_target(const gbb_instance *m, uint8_t op) {
    if (op == 0xC3 || op == 0xC9 || op == 0xCD || op == 0xD9 || op == 0xE9 || (op & 0xC7u) == 0xC7u) return 1;
    if ((op & 0xE7u) == 0xC0u || (op & 0xE7u) == 0xC2u || (op & 0xE7u) == 0xC4u)
        return condition_true(m, (op >> 3) & 3u);
    return 0;
}

static gbb_run_result gbb_run_internal(gbb_instance *instance, uint64_t budget_half_dots,
                                       gbb_trace_record *trace, size_t trace_capacity) {
    gbb_run_result result={0, GBB_STOP_BUDGET, 0, 0, 0, 0};
    if (instance == NULL || !instance->loaded || (trace == NULL && trace_capacity != 0)) { result.reason=GBB_STOP_INVALID_STATE; return result; }
    if (budget_half_dots != 0) apply_input_events_now(instance);
    while (result.consumed_half_dots < budget_half_dots) {
        if (instance->locked) { result.reason=GBB_STOP_LOCKUP; result.lockup_pc=instance->lockup_pc; result.lockup_opcode=instance->lockup_opcode; return result; }
        if (instance->stopped) {
            uint64_t remaining = budget_half_dots - result.consumed_half_dots;
            uint64_t available = UINT64_MAX - instance->time_half_dots;
            uint64_t step = remaining < available ? remaining : available;
            if (instance->input_event_count != 0) {
                uint64_t deadline = instance->input_events[0].at_half_dots;
                uint64_t until_event = deadline - instance->time_half_dots;
                if (until_event <= step) step = until_event;
            }
            if (step != 0) {
                instance->time_half_dots += step;
                result.consumed_half_dots += step;
                apply_input_events_now(instance);
            }
            if (instance->stopped) {
                result.reason = step < remaining && instance->time_half_dots == UINT64_MAX
                    ? GBB_STOP_INVALID_STATE : GBB_STOP_STOPPED;
                return result;
            }
            if (result.consumed_half_dots == budget_half_dots) {
                result.reason = GBB_STOP_NO_PROGRESS;
                return result;
            }
            continue;
        }
        unsigned interrupt = instance->ime ? pending_interrupt(instance) : 5;
        if (interrupt < 5) {
            if (40u > budget_half_dots - result.consumed_half_dots) return result;
            if (UINT64_MAX - instance->time_half_dots < 40u) { result.reason=GBB_STOP_INVALID_STATE; return result; }
            gbb_diagnostic_record operation[GBB_DIAGNOSTIC_OPERATION_RESERVE];
            if (instance->diagnostic_output != NULL &&
                instance->diagnostic_output_capacity - instance->diagnostic_output_count < GBB_DIAGNOSTIC_OPERATION_RESERVE) {
                result.reason=GBB_STOP_OUTPUT_FULL; return result;
            }
            diagnostic_begin(instance, operation, instance->pc, 0);
            instance->instruction_start_half_dots = instance->time_half_dots;
            enter_interrupt(instance, interrupt);
            advance_devices_to(instance, instance->instruction_start_half_dots + 40u);
            diagnostic_commit(instance);
            result.consumed_half_dots += 40;
            continue;
        }
        if (instance->halted) {
            if ((instance->ie & instance->interrupt_flags & 0x1Fu) != 0) {
                instance->halted=0;
                result.reason=GBB_STOP_BUDGET;
                continue;
            }
            if (budget_half_dots - result.consumed_half_dots < 8u) return result;
            if (UINT64_MAX - instance->time_half_dots < 8u) { result.reason=GBB_STOP_INVALID_STATE; return result; }
            /* HALT samples wake conditions at each machine-cycle boundary.
             * A timer/serial interrupt midway through a long budget must wake
             * at the same boundary as it does through shorter run calls. */
            advance_devices(instance, 8u);
            result.consumed_half_dots += 8u;
            result.reason=GBB_STOP_HALTED_IDLE;
            if ((instance->ie & instance->interrupt_flags & 0x1Fu) != 0) {
                instance->halted=0;
                result.reason=GBB_STOP_BUDGET;
            }
            continue;
        }
        if (!read_supported(instance->pc)) { result.reason=GBB_STOP_UNSUPPORTED_BUS; return result; }
        uint8_t opcode = read8(instance, instance->pc);
        /* CB decoding consumes its extension byte, so check it before decode. */
        if (opcode == 0xCB && !read_supported(instruction_address(instance, instance->pc, 1))) {
            result.reason=GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
        decoded d=decode(instance);
        if (!d.supported) {
            instance->locked=1; instance->lockup_pc=instance->pc; instance->lockup_opcode=read8(instance,instance->pc);
            result.reason=GBB_STOP_LOCKUP; result.lockup_pc=instance->lockup_pc; result.lockup_opcode=instance->lockup_opcode; return result;
        }
        if (!instruction_reads_supported(instance, d, opcode)) {
            result.reason = GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
        uint8_t cost=instruction_cost(instance,d);
        if (cost > budget_half_dots-result.consumed_half_dots) return result;
        if (UINT64_MAX - instance->time_half_dots < cost) {
            result.reason = GBB_STOP_INVALID_STATE;
            return result;
        }
        if (trace != NULL && result.trace_count == trace_capacity) { result.reason=GBB_STOP_TRACE_FULL; return result; }
        gbb_diagnostic_record operation[GBB_DIAGNOSTIC_OPERATION_RESERVE];
        if (instance->diagnostic_output != NULL &&
            instance->diagnostic_output_capacity - instance->diagnostic_output_count < GBB_DIAGNOSTIC_OPERATION_RESERVE) {
            result.reason=GBB_STOP_OUTPUT_FULL; return result;
        }
        if (trace != NULL) save_trace(instance,d,&trace[result.trace_count++]);
        int consume_halt_bug=instance->halt_bug;
        int keeps_control_target=consume_halt_bug && halt_bug_keeps_control_target(instance,opcode);
        instance->instruction_start_half_dots = instance->time_half_dots;
        diagnostic_begin(instance, operation, instance->pc, opcode);
        execute(instance,cost);
        advance_devices_to(instance, instance->instruction_start_half_dots + cost);
        if (instance->dma_start_pending) dma_start(instance);
        if (consume_halt_bug) {
            if (!keeps_control_target) instance->pc=(uint16_t)(instance->pc-1u);
            instance->halt_bug=0;
        }
        result.consumed_half_dots += cost;
        diagnostic_commit(instance);
        if (instance->ime_delay != 0 && --instance->ime_delay == 0) instance->ime = 1;
        if (instance->stopped) {
            instance->divider_counter = 0;
            instance->div = 0;
            instance->divider_phase = 0;
            timer_set_signal(instance, timer_input(instance), instance->time_half_dots);
            result.reason=GBB_STOP_STOPPED;
            return result;
        }
        if (instance->serial_unsupported) {
            instance->serial_unsupported = 0;
            result.reason = GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
        if (instance->halted) { result.reason=GBB_STOP_HALTED_IDLE; return result; }
    }
    return result;
}

gbb_run_result gbb_run_ex(gbb_instance *instance, uint64_t budget_half_dots,
                          gbb_trace_record *trace, size_t trace_capacity,
                          gbb_diagnostic_record *diagnostics, size_t diagnostic_capacity) {
    gbb_run_result invalid={0, GBB_STOP_INVALID_STATE, 0, 0, 0, 0};
    if ((diagnostics == NULL && diagnostic_capacity != 0) ||
        (instance != NULL && instance->diagnostic_output != NULL)) return invalid;
    if (instance != NULL) {
        instance->diagnostic_output = diagnostics;
        instance->diagnostic_output_capacity = diagnostic_capacity;
        instance->diagnostic_output_count = 0;
        instance->diagnostic_operation = NULL;
    }
    gbb_run_result result=gbb_run_internal(instance, budget_half_dots, trace, trace_capacity);
    if (instance != NULL) {
        result.diagnostic_count = instance->diagnostic_output_count;
        instance->diagnostic_output = NULL;
        instance->diagnostic_output_capacity = 0;
        instance->diagnostic_operation = NULL;
    }
    return result;
}

gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity) {
    return gbb_run_ex(instance, budget_half_dots, trace, trace_capacity, NULL, 0);
}

uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address) {
    if (instance == NULL) return 0xFF;
    if (address >= 0xC000 && address <= 0xDFFF) return instance->wram[address - 0xC000];
    if (address >= 0xE000 && address <= 0xFDFF) return instance->wram[address - 0xE000];
    if (address >= 0xFF80 && address <= 0xFFFE) return instance->hram[address - 0xFF80];
    return 0xFF;
}
