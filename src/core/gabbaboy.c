#include "gabbaboy/gabbaboy.h"
#include "gabbaboy_test.h"

#include <stdlib.h>
#include <string.h>

#ifndef GBB_P13_MUT
#define GBB_P13_MUT(n) 0u
#endif
#ifndef GBB_P13_DURATION_OFFSET
#define GBB_P13_DURATION_OFFSET 0
#endif
#ifndef GBB_TEST_CGB_PCM_SWAP_NIBBLES
#define GBB_TEST_CGB_PCM_SWAP_NIBBLES 0
#endif
#ifndef GBB_TEST_CGB_PCM_ROUTING_COUPLED
#define GBB_TEST_CGB_PCM_ROUTING_COUPLED 0
#endif
#ifndef GBB_TEST_CGB_PCM_WRITABLE
#define GBB_TEST_CGB_PCM_WRITABLE 0
#endif


#define GBB_INPUT_EVENT_CAPACITY 64u
#define GBB_DIAGNOSTIC_OPERATION_RESERVE 16u
#define GBB_FRAME_WIDTH 160u
#define GBB_FRAME_HEIGHT 144u
#define GBB_FRAME_PIXELS (GBB_FRAME_WIDTH * GBB_FRAME_HEIGHT)
#define GBB_OAM_BYTES 160u
#define GBB_VRAM_BANKS 2u
#define GBB_VRAM_BANK_SIZE 8192u
#define GBB_WRAM_BANKS 8u
#define GBB_WRAM_BANK_SIZE 4096u
/* Half-dot timeline (D-070): one uint64_t half-dot counter is the single clock for normal and
 * double speed. A CPU T-cycle is 2 half-dots normal, 1 double; a PPU dot is always 2. */
#define GBB_MASTER_HALF_DOTS_PER_SECOND UINT64_C(8388608)
#define GBB_HALF_DOTS_PER_T_NORMAL 2u
#define GBB_HALF_DOTS_PER_T_DOUBLE 1u
#define GBB_T_PER_M 4u
/* SameBoy 0x20008 minus its 4 T IME=0 adjustment; confirmed in committed-core window
 * [0x20004,0x20007] at revision 2e78a48 and re-measured by age_stall_window. */
#define GBB_SPEED_SWITCH_STALL_T 0x20004u
/* 2 M expressed in normal-speed half-dots; instruction_cost applies >> double_speed once. */
#define GBB_STOP_SWITCH_COST_HALF_DOTS 16u
#define GBB_STALL_NONE 0u
#define GBB_STALL_SPEED_SWITCH 1u
#define GBB_STALL_SWITCH_REALIGN 2u
#define GBB_HALF_DOTS_PER_DOT 2u
#define GBB_DOTS_PER_LINE 456u
#define GBB_LINES_PER_FRAME 154u
#define GBB_DMA_BYTE_PERIOD_HALF_DOTS 8u
#define GBB_LINE_OBJECT_LIMIT 10u
#define GBB_PPU_FIFO_CAPACITY 16u
#define GBB_AUDIO_CLOCK_HALF_DOTS UINT64_C(8388608)
#define GBB_AUDIO_SAMPLE_RATE UINT64_C(48000)
#define GBB_AUDIO_EVENT_PHASES 8u
#define GBB_AUDIO_EVENT_TAPS 16u
#define GBB_AUDIO_HPF_Q15 32648
/* Pan Docs maps each DAC to -1..1 (unit = 16384 here) and sums four channels,
 * so a side spans +/-4 units; NR50 then scales it by (volume+1)/8. One s16
 * full scale (32768) must therefore hold 4 units * 8/8, i.e. the product of
 * unit samples and the (volume+1) multiplier (1..8) is divided by 16.
 * Without this headroom one full-volume channel at NR50=$77 was 3.5x s16. */
#define GBB_AUDIO_MIX_HEADROOM_DIV 16
typedef struct {
    uint8_t sweep, duty_length, envelope, frequency_low, control;
    uint16_t length, frequency, timer, sweep_shadow;
    uint8_t phase, volume, envelope_timer, sweep_timer;
    int enabled, sweep_enabled, sweep_negate_used;
} apu_pulse_channel;
typedef struct {
    uint8_t dac, length_reg, level, frequency_low, control;
    uint8_t ram[16], position;
    uint16_t length, timer;
    int enabled;
} apu_wave_channel;
typedef struct {
    uint8_t length_reg, envelope, polynomial, control, volume, envelope_timer;
    uint16_t length, lfsr;
    uint32_t timer;
    int enabled;
} apu_noise_channel;
/* ======================= Cartridge mapper ===================================
 * Every cartridge decision lives in this section. A static const row per
 * accepted cartridge-type byte is looked up once at load; the instance then
 * carries only the plain-integer cart_state, and read8/write8 dispatch with
 * switch (kind). No function pointers: the hot path stays a stored-byte test.
 * ===========================================================================*/
/* MBC5 carts reach 8 MiB (512 banks); every other accepted or unknown type
 * keeps the original 2 MiB early ceiling so its loader result never changes. */
#define GBB_MAX_ROM_SIZE ((size_t)8u * 1024u * 1024u)
#define GBB_LEGACY_MAX_ROM_SIZE ((size_t)2u * 1024u * 1024u)
/* MBC3 ($0F-$13) decodes seven ROM bank bits; ROM code $07 (4 MiB) is the MBC30
 * variant and is rejected after the checksum, so 4 MiB is only the early ceiling. */
#define GBB_MBC3_MAX_ROM_SIZE ((size_t)4u * 1024u * 1024u)

/* ROM_ONLY must stay 0 so a calloc-zeroed instance is a ROM-only cartridge. */
typedef enum { CART_ROM_ONLY = 0, CART_MBC1 = 1, CART_MBC2 = 2, CART_MBC5 = 3,
       CART_MBC3 = 4 } cart_kind;

typedef enum {
    CART_RAM_NONE = 0,     /* RAM code must be $00 */
    CART_RAM_8K_OR_32K = 1, /* code $02 = 8 KiB; $03 = 32 KiB on small ROMs */
    CART_RAM_MBC2 = 2,      /* built-in 512 nibbles; header RAM code must be $00 */
    CART_RAM_MBC5 = 3,      /* codes $02/$03/$05/$04 = 8/32/64/128 KiB */
    CART_RAM_MBC3 = 4       /* codes $02/$03 = 8/32 KiB; $05 is the MBC30 marker only */
} cart_ram_rule;

/* MBC2 has 512 x 4-bit cells inside the mapper chip. We store each as a byte
 * in canonical form 0xF0 | nibble, because the upper data lines float high. */
#define MBC2_RAM_BYTES 512u

typedef struct {
    uint8_t kind;
    uint8_t ram_window_mapped;
    uint8_t has_battery;
    uint8_t has_timer;
    uint8_t has_rumble;
    uint8_t rom_bank_lo;
    uint8_t rom_bank_hi;
    uint8_t ram_bank;
    uint8_t ram_enabled;
    uint8_t mbc1_mode;
    uint8_t rumble_on;
    uint64_t rumble_changes;
    /* MBC3 RTC (D-07): lazy, anchored on emulated time_half_dots. The live
     * registers hold the clock as of rtc_synced_at; rtc_l holds the bytes the
     * guest reads (S, M, H, DL, DH) until the next latch. rtc_sub counts
     * half-dots inside the current second (< 2^23). */
    uint8_t rtc_s, rtc_m, rtc_h, rtc_dl, rtc_dh;
    uint8_t rtc_l[5];
    uint8_t rtc_latch_prev;
    uint32_t rtc_sub;
    uint64_t rtc_synced_at;
} cart_state;

typedef struct {
    uint8_t type;
    uint8_t kind;
    uint8_t ram_window_mapped;
    uint8_t has_battery;
    uint8_t has_timer;
    uint8_t has_rumble;
    uint8_t max_rom_code;
    uint8_t ram_rule;
    uint8_t ram32_max_rom_code; /* MBC1: 32 KiB RAM needs a ROM code at most this */
    size_t early_ceiling_bytes; /* ROM size ceiling checked before type support */
} cart_type_row;

static const cart_type_row cart_type_table[] = {
    /* type kind          window batt timer rumble maxrom ram rule           ram32 ceiling */
    { 0x00u, CART_ROM_ONLY, 0u, 0u, 0u, 0u, 0x00u, CART_RAM_NONE,      0u,    GBB_LEGACY_MAX_ROM_SIZE },
    { 0x01u, CART_MBC1,     1u, 0u, 0u, 0u, 0x06u, CART_RAM_NONE,      0u,    GBB_LEGACY_MAX_ROM_SIZE },
    { 0x02u, CART_MBC1,     1u, 0u, 0u, 0u, 0x06u, CART_RAM_8K_OR_32K, 0x04u, GBB_LEGACY_MAX_ROM_SIZE },
    { 0x03u, CART_MBC1,     1u, 1u, 0u, 0u, 0x06u, CART_RAM_8K_OR_32K, 0x04u, GBB_LEGACY_MAX_ROM_SIZE },
    { 0x05u, CART_MBC2,     1u, 0u, 0u, 0u, 0x03u, CART_RAM_MBC2,      0u,    GBB_LEGACY_MAX_ROM_SIZE },
    { 0x06u, CART_MBC2,     1u, 1u, 0u, 0u, 0x03u, CART_RAM_MBC2,      0u,    GBB_LEGACY_MAX_ROM_SIZE },
    { 0x0Fu, CART_MBC3,     1u, 1u, 1u, 0u, 0x07u, CART_RAM_NONE,      0u,    GBB_MBC3_MAX_ROM_SIZE },
    { 0x10u, CART_MBC3,     1u, 1u, 1u, 0u, 0x07u, CART_RAM_MBC3,      0u,    GBB_MBC3_MAX_ROM_SIZE },
    { 0x11u, CART_MBC3,     1u, 0u, 0u, 0u, 0x07u, CART_RAM_NONE,      0u,    GBB_MBC3_MAX_ROM_SIZE },
    { 0x12u, CART_MBC3,     1u, 0u, 0u, 0u, 0x07u, CART_RAM_MBC3,      0u,    GBB_MBC3_MAX_ROM_SIZE },
    { 0x13u, CART_MBC3,     1u, 1u, 0u, 0u, 0x07u, CART_RAM_MBC3,      0u,    GBB_MBC3_MAX_ROM_SIZE },
    { 0x19u, CART_MBC5,     1u, 0u, 0u, 0u, 0x08u, CART_RAM_NONE,      0u,    GBB_MAX_ROM_SIZE },
    { 0x1Au, CART_MBC5,     1u, 0u, 0u, 0u, 0x08u, CART_RAM_MBC5,      0u,    GBB_MAX_ROM_SIZE },
    { 0x1Bu, CART_MBC5,     1u, 1u, 0u, 0u, 0x08u, CART_RAM_MBC5,      0u,    GBB_MAX_ROM_SIZE },
    { 0x1Cu, CART_MBC5,     1u, 0u, 0u, 1u, 0x08u, CART_RAM_NONE,      0u,    GBB_MAX_ROM_SIZE },
    { 0x1Du, CART_MBC5,     1u, 0u, 0u, 1u, 0x08u, CART_RAM_MBC5,      0u,    GBB_MAX_ROM_SIZE },
    { 0x1Eu, CART_MBC5,     1u, 1u, 0u, 1u, 0x08u, CART_RAM_MBC5,      0u,    GBB_MAX_ROM_SIZE },
};

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static const cart_type_row *cart_row_for_type(uint8_t type) {
    for (size_t i = 0; i < sizeof(cart_type_table) / sizeof(cart_type_table[0]); ++i)
        if (cart_type_table[i].type == type) return &cart_type_table[i];
    return NULL;
}

/* Mapper registers only. Never touches cartridge RAM, battery generation, kind
 * or flags, and is safe on an unloaded (calloc-zeroed) instance. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static void cart_reset_registers(cart_state *c) {
    c->rom_bank_lo = 1u;
    c->rom_bank_hi = 0u;
    c->ram_bank = 0u;
    c->ram_enabled = 0u;
    c->mbc1_mode = 0u;
    c->rtc_latch_prev = 0xFFu; /* a single $01 after load or reset never latches */
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static size_t mbc1_rom_bank(const cart_state *c, size_t rom_size, uint16_t address) {
    const size_t mask = rom_size / 0x4000u - 1u;
    if (address < 0x4000u)
        return c->mbc1_mode ? ((size_t)c->rom_bank_hi << 5) & mask : 0u;

    /* Translate zero before masking: a small ROM can disconnect upper lines. */
    const size_t low = c->rom_bank_lo == 0u ? 1u : c->rom_bank_lo;
    return (((size_t)c->rom_bank_hi << 5) | low) & mask;
}

/* MBC5 has two independent ROM bank registers: $2000-$2FFF holds the low eight
 * bits and $3000-$3FFF bit 8. Bank 0 is a legal selection for $4000-$7FFF (no
 * 0-to-1 remap), and a bank beyond the image wraps by masking. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static size_t mbc5_rom_bank(const cart_state *c, size_t rom_banks) {
    return ((((size_t)(c->rom_bank_hi & 1u) << 8) | c->rom_bank_lo) & (rom_banks - 1u));
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static size_t mbc1_ram_offset(const cart_state *c, size_t ram_size, uint16_t address) {
    const size_t bank_size = 0x2000u;
    const size_t bank_count = ram_size / bank_size;
    const size_t bank = c->mbc1_mode && bank_count > 1u
        ? ((size_t)c->rom_bank_hi & (bank_count - 1u)) : 0u;
    return bank * bank_size + (size_t)(address - 0xA000u);
}

/* ---- MBC3 RTC (D-07..D-09) --------------------------------------------------
 * The clock never reads the host: it is advanced only from the emulated
 * half-dot counter, lazily, when the guest touches a clock register. 2^23
 * half-dots are exactly one second (4194304 Hz * 2 half-dots per T-cycle). */
#define RTC_HALF_DOTS_PER_SECOND_SHIFT 23u

_Static_assert(GBB_MASTER_HALF_DOTS_PER_SECOND == (UINT64_C(1) << 23) &&
               GBB_MASTER_HALF_DOTS_PER_SECOND == GBB_AUDIO_CLOCK_HALF_DOTS,
               "half-dot timeline: master rate must be 2^23 half-dots per second");
_Static_assert(GBB_HALF_DOTS_PER_T_NORMAL == 2u,
               "half-dot timeline: a normal-speed T-cycle is 2 half-dots");
_Static_assert(GBB_HALF_DOTS_PER_T_DOUBLE == 1u,
               "half-dot timeline: a double-speed T-cycle is 1 half-dot");
_Static_assert(GBB_T_PER_M == 4u, "half-dot timeline: an M-cycle is 4 T-cycles");
_Static_assert(GBB_SPEED_SWITCH_STALL_T % GBB_T_PER_M == 0u,
               "half-dot timeline: the speed-switch stall is a whole number of M-cycles");
_Static_assert(GBB_HALF_DOTS_PER_DOT == 2u, "half-dot timeline: a PPU dot is 2 half-dots");
_Static_assert(RTC_HALF_DOTS_PER_SECOND_SHIFT == 23u,
               "half-dot timeline: the RTC counts 2^23 half-dots per second");
_Static_assert(GBB_DOTS_PER_LINE * GBB_LINES_PER_FRAME * GBB_HALF_DOTS_PER_DOT == 140448u,
               "half-dot timeline: a frame is 140448 half-dots");
_Static_assert(GBB_DMA_BYTE_PERIOD_HALF_DOTS == GBB_T_PER_M * GBB_HALF_DOTS_PER_T_NORMAL,
               "half-dot timeline: an OAM DMA byte takes one normal-speed M-cycle");
#define RTC_SUB_MASK 0x7FFFFFu

/* Add n ticks to a field that carries at `limit` and stores `mask` bits. A value
 * at or above the limit (only reachable by a guest write) is not a legal count:
 * it steps to (v + 1) & mask without carrying until it wraps to 0, and only then
 * counts normally. Returns the number of carries into the next field. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static uint64_t rtc_step_field(uint8_t *field, uint64_t n, uint32_t limit, uint32_t mask) {
    uint64_t f = *field;
    if (f >= limit) {
        const uint64_t to_wrap = (uint64_t)mask + 1u - f;
        if (n < to_wrap) {
            *field = (uint8_t)(f + n);
            return 0u;
        }
        n -= to_wrap;
        f = 0u;
    }
    /* Split n first so f + n can never wrap even for a 64-bit second count. */
    const uint64_t low = f + n % limit;
    *field = (uint8_t)(low % limit);
    return n / limit + low / limit;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static void rtc_add_seconds(cart_state *c, uint64_t secs) {
    if (secs == 0u) return;
    const uint64_t minutes = rtc_step_field(&c->rtc_s, secs, 60u, 0x3Fu);
    const uint64_t hours = rtc_step_field(&c->rtc_m, minutes, 60u, 0x3Fu);
    const uint64_t days = rtc_step_field(&c->rtc_h, hours, 24u, 0x1Fu);
    const uint64_t total = (uint64_t)c->rtc_dl + ((uint64_t)(c->rtc_dh & 0x01u) * 256u) + days;
    if (total >= 512u) c->rtc_dh |= 0x80u; /* sticky until a guest DH write clears it */
    c->rtc_dl = (uint8_t)(total & 0xFFu);
    c->rtc_dh = (uint8_t)((c->rtc_dh & 0xC0u) | (uint8_t)((total >> 8) & 1u));
}

/* Credit the half-dots since the last sync. A halted clock gets no time, but
 * the anchor still advances so un-halting never credits the halted period. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static void rtc_sync(cart_state *c, uint64_t now) {
    const uint64_t el = now >= c->rtc_synced_at ? now - c->rtc_synced_at : 0u;
    c->rtc_synced_at = now;
    if (c->rtc_dh & 0x40u) return;
    const uint64_t low = (el & RTC_SUB_MASK) + c->rtc_sub;
    const uint64_t secs = (el >> RTC_HALF_DOTS_PER_SECOND_SHIFT) + /* P12-M12 */
                          (low >> RTC_HALF_DOTS_PER_SECOND_SHIFT);
    c->rtc_sub = (uint32_t)(low & RTC_SUB_MASK);
    rtc_add_seconds(c, secs);
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static uint8_t rtc_read_mask(unsigned reg, uint8_t value) {
    static const uint8_t masks[5] = {0x3Fu, 0x3Fu, 0x1Fu, 0xFFu, 0xC1u};
    return (uint8_t)(value & masks[reg]);
}

/* Returns 1 when the observable clock state changed (for the D-10 generation). */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static int rtc_write_register(cart_state *c, uint64_t now, unsigned reg, uint8_t value) {
    rtc_sync(c, now);
    const uint8_t b_s = c->rtc_s, b_m = c->rtc_m, b_h = c->rtc_h;
    const uint8_t b_dl = c->rtc_dl, b_dh = c->rtc_dh;
    const uint32_t sub_before = c->rtc_sub;
    switch (reg) {
    case 0u:
        c->rtc_s = (uint8_t)(value & 0x3Fu); /* rtc: out-of-range fields are stored as written */
        c->rtc_sub = 0u; /* rtc: a seconds write restarts the sub-second prescaler */
        break;
    case 1u: c->rtc_m = (uint8_t)(value & 0x3Fu); break;
    case 2u: c->rtc_h = (uint8_t)(value & 0x1Fu); break;
    case 3u: c->rtc_dl = value; break;
    default: c->rtc_dh = (uint8_t)(value & 0xC1u); break;
    }
    if (reg >= 1u && reg <= 3u) c->rtc_sub = sub_before; /* rtc: other register writes keep the prescaler */
    if (reg == 4u) c->rtc_sub = sub_before; /* rtc: a halt toggle keeps the prescaler */
    return b_s != c->rtc_s || b_m != c->rtc_m || b_h != c->rtc_h ||
           b_dl != c->rtc_dl || b_dh != c->rtc_dh || sub_before != c->rtc_sub;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static void rtc_latch_write(cart_state *c, uint64_t now, uint8_t value) {
    const int latch_now = c->rtc_latch_prev == 0x00u && value == 0x01u; /* rtc: latch only on 00 then 01 */
    if (latch_now) {
        rtc_sync(c, now);
        c->rtc_l[0] = c->rtc_s; c->rtc_l[1] = c->rtc_m; c->rtc_l[2] = c->rtc_h;
        c->rtc_l[3] = c->rtc_dl; c->rtc_l[4] = c->rtc_dh;
    }
    c->rtc_latch_prev = value;
}
/* ---- end MBC3 RTC ---------------------------------------------------------- */
/* ===================== end Cartridge mapper ================================ */

typedef struct {
    uint8_t type;
    uint8_t kind;
    uint8_t ram_window_mapped;
    uint8_t has_battery;
    uint8_t has_timer;
    uint8_t has_rumble;
    uint8_t cgb_flag;       /* raw $143 */
    uint8_t cgb_support;    /* a gbb_cgb_support value */
    size_t ram_size;
} cartridge_info;

typedef struct {
    uint8_t mode; /* 0 idle, 1 HBlank transfer, 2 general-purpose transfer */
    uint8_t active; /* one admitted 16-byte block is consuming master time */
    uint8_t pending_hblank;
    uint16_t blocks_remaining;
    uint8_t byte_index;
    uint8_t byte_phase;
    uint16_t source_cursor;
    uint32_t destination_cursor;
    uint8_t block_vram_bank;
    uint8_t source_high, source_low, destination_high, destination_low;
    uint8_t control_readback;
} hdma_state;

_Static_assert(sizeof(gbb_info) == GBB_INFO_SIZE_V1, "gbb_info layout");
_Static_assert(sizeof(gbb_compat_palette) == GBB_COMPAT_PALETTE_SIZE_V1, "gbb_compat_palette layout");

typedef struct gbb_test_dma_event gbb_test_dma_event;

struct gbb_instance {
    uint8_t *rom;
    size_t rom_size;
    uint8_t *cartridge_ram;
    size_t cartridge_ram_size;
    uint64_t battery_generation;
    cart_state cart;
    uint8_t wram[GBB_WRAM_BANKS][GBB_WRAM_BANK_SIZE];
    uint8_t hram[127];
    uint8_t vram[GBB_VRAM_BANKS][GBB_VRAM_BANK_SIZE];
    /* Effective banks. vram_bank is 0 or 1; wram_bank is 1..7 (SVBK 0 selects 1). svbk is the raw
     * 3-bit register. DMG pins 0 and 1 and never changes them. */
    uint8_t vram_bank;
    uint8_t wram_bank;
    uint8_t svbk;
    /* CGB-profile I/O register state (Plan 10-09). key1_armed is KEY1 bit 0. bcps/ocps are the palette index registers, ff72-ff75 the
     * undocumented CGB scratch registers. DMG never reads or writes any of these. */
    uint8_t key1_armed, bcps, ocps, ff72, ff73, ff74, ff75;
    uint8_t double_speed, cpu_stall_kind, stop_switch_pending;
    uint32_t cpu_stall_half_dots;
    /* CGB palette RAM (Phase 11): 8 palettes of 4 little-endian RGB555 colours per side, addressed
     * through BCPS/OCPS bits 0-5. opri is the stored OPRI bit 0; it never changes object order after
     * boot (D-08), which exec_mode decides. */
    uint8_t bg_cram[64], obj_cram[64], opri;
    uint8_t oam[GBB_OAM_BYTES];
    uint8_t frame_working[GBB_FRAME_PIXELS];
    uint8_t frame_completed[GBB_FRAME_PIXELS];
    /* CGB-mode RGB555 frames (Phase 11, D-02). In CGB mode only rgb_working is written per dot and
     * the shade buffers stay zero; on the DMG profile only the shade buffers are written. Both
     * pairs share frame_generation and frame_completion_half_dots. */
    uint16_t rgb_working[GBB_FRAME_PIXELS];
    uint16_t rgb_completed[GBB_FRAME_PIXELS];
    /* Compat palette (D-17): sets BG, OBJ0, OBJ1 by shade. Instance configuration, set in
     * gbb_create and never in reset_state, so it survives reset and ROM load. */
    uint16_t compat_rgb555[3][4];
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
    hdma_state hdma;
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
    apu_pulse_channel apu_pulse[2];
    apu_wave_channel apu_wave;
    apu_noise_channel apu_noise;
    uint8_t apu_nr50, apu_nr51, apu_power, apu_sequencer_step;
#if GBB_TEST_CGB_PCM_WRITABLE
    uint8_t apu_pcm_test_override[2], apu_pcm_test_override_valid;
#endif
    uint64_t apu_sample_phase;
    int64_t audio_event_ring[2][GBB_AUDIO_EVENT_TAPS];
    uint8_t audio_event_head;
    int32_t audio_mix_level[2];
    int32_t audio_hpf_input[2];
    int32_t audio_hpf_output[2];
    gbb_audio_frame *audio_frames;
    size_t audio_frame_capacity;
    size_t audio_frame_count;
    int audio_run_active;
    int timer_signal;
    int timer_reload_pending;
    uint8_t timer_reload_remaining;
    uint64_t timer_reloaded_at;
    uint64_t instruction_start_half_dots;
    uint16_t serial_edge_remaining;
    int serial_active;
    /* Deferred-access latch (OQ5): set by a write the core refuses to model (serial while a
     * transfer is active, or a DEFERRED CGB register); reported as GBB_STOP_UNSUPPORTED_BUS after
     * the instruction retires. bus_unsupported_address is the refused address (a failed read
     * pre-flight records its address here too, with no other state change). */
    int bus_unsupported;
    uint16_t bus_unsupported_address;
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
    uint8_t profile;        /* fixed at gbb_create */
    uint8_t exec_mode;      /* a gbb_exec_mode value; committed with the ROM swap */
    uint8_t cgb_flag;       /* raw $143 of the loaded ROM */
    uint8_t cgb_support;
    uint8_t cartridge_type; /* raw $147 of the loaded ROM */
    gbb_diagnostic_record *diagnostic_output;
    size_t diagnostic_output_capacity;
    size_t diagnostic_output_count;
    gbb_diagnostic_record *diagnostic_operation;
    size_t diagnostic_operation_count;
    uint16_t diagnostic_pc;
    uint8_t diagnostic_opcode;
};

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
static int16_t audio_saturate_s16(int64_t value) {
    if (value > INT16_MAX) value = INT16_MAX;
    if (value < INT16_MIN) value = INT16_MIN;
    return (int16_t)value;
}

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
static int64_t audio_round_q15(int64_t value) {
    if (value >= 0) return (value + 16384) / 32768;
    return -((-value + 16384) / 32768);
}

/* Bounded 8-phase, 16-sample windowed-sinc step responses in Q15. */
static const int16_t audio_step_q15[GBB_AUDIO_EVENT_PHASES][GBB_AUDIO_EVENT_TAPS] = {
    {16384, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767},
    {14336, 18431, 22527, 26623, 29695, 31743, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767},
    {12288, 16384, 20480, 24575, 28671, 30719, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767},
    {10240, 14336, 18431, 22527, 26623, 29695, 31743, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767},
    {8192, 12288, 16384, 20480, 24575, 28671, 30719, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767},
    {6144, 10240, 14336, 18431, 22527, 26623, 29695, 31743, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767},
    {4096, 8192, 12288, 16384, 20480, 24575, 28671, 30719, 32767, 32767, 32767, 32767, 32767, 32767, 32767, 32767}
};

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
static void audio_add_edge(gbb_instance *m, unsigned channel, int32_t delta,
                           unsigned phase) {
    for (unsigned tap = 0u; tap < GBB_AUDIO_EVENT_TAPS; ++tap) {
        const unsigned slot = ((unsigned)m->audio_event_head + tap) % GBB_AUDIO_EVENT_TAPS;
        const int64_t contribution = (int64_t)delta *
            ((int32_t)audio_step_q15[phase][tap] - 32767);
        m->audio_event_ring[channel][slot] += contribution;
    }
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static gbb_audio_frame audio_process_sample(gbb_instance *m) {
    int16_t output[2];
    for (unsigned channel = 0u; channel < 2u; ++channel) {
        const unsigned slot = m->audio_event_head;
        const int64_t sample = audio_saturate_s16(audio_round_q15(
            (int64_t)m->audio_mix_level[channel] * 32768 +
            m->audio_event_ring[channel][slot]));
        m->audio_event_ring[channel][slot] = 0;
        /* MODEL: UNKNOWN GATE-01 research:14 -- high-pass filter constant differs by model */
        const int64_t hp = sample - m->audio_hpf_input[channel] +
            audio_round_q15((int64_t)m->audio_hpf_output[channel] * GBB_AUDIO_HPF_Q15);
        m->audio_hpf_input[channel] = audio_saturate_s16(sample);
        m->audio_hpf_output[channel] = (int32_t)audio_saturate_s16(hp);
        output[channel] = (int16_t)m->audio_hpf_output[channel];
    }
    m->audio_event_head = (uint8_t)((m->audio_event_head + 1u) % GBB_AUDIO_EVENT_TAPS);
    return (gbb_audio_frame){output[0], output[1]};
}

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
static void audio_current_mix(const gbb_instance *m, int32_t *left, int32_t *right) {
    static const uint8_t duty_pattern[4] = {0x01u, 0x81u, 0x87u, 0x7Eu};
    *left = 0; *right = 0;
    for (unsigned i = 0u; i < 2u; ++i) {
        const apu_pulse_channel *pulse = &m->apu_pulse[i];
        const uint8_t duty = (uint8_t)(pulse->duty_length >> 6);
        int32_t sample = 0;
        if (pulse->enabled && pulse->volume != 0u &&
            ((duty_pattern[duty] >> pulse->phase) & 1u) != 0u)
            sample = (int32_t)pulse->volume * 2048 - 16384;
        if ((m->apu_nr51 & (1u << i)) != 0u)
            *right += sample * (int32_t)((m->apu_nr50 & 7u) + 1u) / GBB_AUDIO_MIX_HEADROOM_DIV;
        if ((m->apu_nr51 & (1u << (i + 4u))) != 0u)
            *left += sample * (int32_t)(((m->apu_nr50 >> 4) & 7u) + 1u) / GBB_AUDIO_MIX_HEADROOM_DIV;
    }
    int32_t wave_sample = 0;
    if (m->apu_wave.enabled && m->apu_wave.level != 0u) {
        const uint8_t packed = m->apu_wave.ram[m->apu_wave.position >> 1];
        const uint8_t digital = (m->apu_wave.position & 1u) == 0u
            ? (uint8_t)(packed >> 4) : (uint8_t)(packed & 0x0Fu);
        const unsigned shift = (m->apu_wave.level >> 5) - 1u;
        wave_sample = (int32_t)(digital >> shift) * 2048 - 16384;
    }
    if ((m->apu_nr51 & 0x04u) != 0u)
        *right += wave_sample * (int32_t)((m->apu_nr50 & 7u) + 1u) / GBB_AUDIO_MIX_HEADROOM_DIV;
    if ((m->apu_nr51 & 0x40u) != 0u)
        *left += wave_sample * (int32_t)(((m->apu_nr50 >> 4) & 7u) + 1u) / GBB_AUDIO_MIX_HEADROOM_DIV;
    int32_t noise_sample = 0;
    if (m->apu_noise.enabled && m->apu_noise.volume != 0u &&
        (m->apu_noise.lfsr & 1u) == 0u)
        noise_sample = (int32_t)m->apu_noise.volume * 2048 - 16384;
    if ((m->apu_nr51 & 0x08u) != 0u)
        *right += noise_sample * (int32_t)((m->apu_nr50 & 7u) + 1u) / GBB_AUDIO_MIX_HEADROOM_DIV;
    if ((m->apu_nr51 & 0x80u) != 0u)
        *left += noise_sample * (int32_t)(((m->apu_nr50 >> 4) & 7u) + 1u) / GBB_AUDIO_MIX_HEADROOM_DIV;
}

/* CGB PCM readback is the digital DAC input, before NR50/NR51 routing and host mixing. */
static uint8_t apu_digital_output(const gbb_instance *m, unsigned channel) {
    static const uint8_t duty_pattern[4] = {0x01u, 0x81u, 0x87u, 0x7Eu};
    if (!m->apu_power) return 0u;
#if GBB_TEST_CGB_PCM_ROUTING_COUPLED
    if ((m->apu_nr51 & (uint8_t)((1u << channel) | (1u << (channel + 4u)))) == 0u)
        return 0u;
#endif
    if (channel < 2u) {
        const apu_pulse_channel *pulse = &m->apu_pulse[channel];
        const unsigned duty = pulse->duty_length >> 6;
        return pulse->enabled && (pulse->envelope & 0xF8u) != 0u &&
               pulse->volume != 0u && ((duty_pattern[duty] >> pulse->phase) & 1u) != 0u
            ? pulse->volume : 0u;
    }
    if (channel == 2u) {
        const apu_wave_channel *wave = &m->apu_wave;
        if (!wave->enabled || (wave->dac & 0x80u) == 0u || wave->level == 0u) return 0u;
        const uint8_t packed = wave->ram[wave->position >> 1];
        const uint8_t sample = (wave->position & 1u) == 0u
            ? (uint8_t)(packed >> 4) : (uint8_t)(packed & 0x0Fu);
        return (uint8_t)(sample >> ((wave->level >> 5) - 1u));
    }
    if (channel == 3u) {
        const apu_noise_channel *noise = &m->apu_noise;
        return noise->enabled && (noise->envelope & 0xF8u) != 0u &&
               noise->volume != 0u && (noise->lfsr & 1u) == 0u
            ? noise->volume : 0u;
    }
    return 0u;
}

static uint8_t apu_pcm_read(const gbb_instance *m, uint16_t address) {
    const unsigned first = address == 0xFF76u ? 0u : 2u;
#if GBB_TEST_CGB_PCM_WRITABLE
    const unsigned register_index = address == 0xFF76u ? 0u : 1u;
    if ((m->apu_pcm_test_override_valid & (uint8_t)(1u << register_index)) != 0u)
        return m->apu_pcm_test_override[register_index];
#endif
    const uint8_t low = apu_digital_output(m, first);
    const uint8_t high = apu_digital_output(m, first + 1u);
    uint8_t value = (uint8_t)((high << 4) | (low & 0x0Fu));
#if GBB_TEST_CGB_PCM_SWAP_NIBBLES
    value = (uint8_t)((value << 4) | (value >> 4));
#endif
    return value;
}

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
void gbb_test_audio_kernel(gbb_instance *m, const int32_t *left,
                           const int32_t *right, size_t count,
                           gbb_audio_frame *output) {
    if (m == NULL || left == NULL || right == NULL || output == NULL) return;
    for (size_t i = 0u; i < count; ++i) {
        audio_add_edge(m, 0u, left[i] - m->audio_mix_level[0], 0u);
        audio_add_edge(m, 1u, right[i] - m->audio_mix_level[1], 0u);
        m->audio_mix_level[0] = left[i]; m->audio_mix_level[1] = right[i];
        output[i] = audio_process_sample(m);
    }
}

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
void gbb_test_audio_edge(gbb_instance *m, int32_t left_delta, int32_t right_delta,
                         unsigned phase, gbb_audio_frame *output) {
    if (m == NULL || output == NULL || phase >= GBB_AUDIO_EVENT_PHASES) return;
    audio_add_edge(m, 0u, left_delta, phase);
    audio_add_edge(m, 1u, right_delta, phase);
    m->audio_mix_level[0] += left_delta;
    m->audio_mix_level[1] += right_delta;
    *output = audio_process_sample(m);
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
static uint8_t diagnostic_timer_state(const gbb_instance *m) {
    return (uint8_t)((m->tac & 7u) | (m->timer_reload_pending ? 0x08u : 0u) |
                     (m->timer_signal ? 0x10u : 0u));
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
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

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
static void diagnostic_begin(gbb_instance *m, gbb_diagnostic_record records[GBB_DIAGNOSTIC_OPERATION_RESERVE], uint16_t pc, uint8_t opcode) {
    if (m->diagnostic_output == NULL) return;
    m->diagnostic_operation = records;
    m->diagnostic_operation_count = 0;
    m->diagnostic_pc = pc;
    m->diagnostic_opcode = opcode;
    diagnostic_add(m, GBB_DIAGNOSTIC_INSTRUCTION, m->time_half_dots, 0, opcode);
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
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

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
void gbb_test_observer_set(gbb_instance *m, gbb_test_bus_event *events, size_t capacity) {
    if (m == NULL) return;
    m->test_events = events;
    m->test_event_capacity = capacity;
    m->test_event_count = 0;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
size_t gbb_test_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_event_count;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
void gbb_test_ppu_observer_set(gbb_instance *m, gbb_test_bus_event *events,
                               size_t capacity) {
    if (m == NULL) return;
    m->test_ppu_events = events;
    m->test_ppu_event_capacity = capacity;
    m->test_ppu_event_count = 0;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
size_t gbb_test_ppu_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_ppu_event_count;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
void gbb_test_dma_observer_set(gbb_instance *m, gbb_test_dma_event *events,
                               size_t capacity) {
    if (m == NULL) return;
    m->test_dma_events = events;
    m->test_dma_event_capacity = capacity;
    m->test_dma_event_count = 0;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
size_t gbb_test_dma_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_dma_event_count;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
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

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
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
static int model_is_cgb(const gbb_instance *m);
static void hdma_request(gbb_instance *m);
static void speed_switch_apply_realign(gbb_instance *m);

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void ppu_set_mode(gbb_instance *m, uint8_t mode) {
    if (m->ppu_mode != mode) {
        const uint8_t previous_mode = m->ppu_mode;
        m->ppu_mode = mode;
        observe_ppu(m, 0xFF41, 4, mode);
        /* MODEL: CGB_ONLY GATE-91 GUARD=model_is_cgb -- ordinary HBlank DMA requests only on a visible mode-3-to-0 edge */
        if (model_is_cgb(m) && previous_mode == 3u && mode == 0u &&
            (m->lcdc & 0x80u) != 0u &&
            m->ly < GBB_FRAME_HEIGHT)
            hdma_request(m);
        else if (GBB_P13_MUT(49) && model_is_cgb(m) &&
                 previous_mode == 3u && mode == 0u) { /* P13-05-M10: false HBlank trigger */
            hdma_request(m);
        }
        ppu_update_stat_line(m);
    }
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void ppu_update_stat_line(gbb_instance *m) {
    int line = 0;
    if ((m->lcdc & 0x80u) != 0) {
        line = (((m->ppu_mode == 0u) && ((m->stat & 0x08u) != 0)) ||
                ((m->ppu_mode == 1u) && ((m->stat & 0x10u) != 0)) ||
                ((m->ppu_mode == 2u) && ((m->stat & 0x20u) != 0)) ||
                ((m->ly == m->lyc) && ((m->stat & 0x40u) != 0)));
    }
    /* MODEL: UNKNOWN GATE-02 research:14 -- STAT interrupt line edge timing on CGB is unresearched; deferred by D-09/D-12 */
    if (line && !m->ppu_stat_line) {
        m->interrupt_flags |= 0x02u;
        observe_ppu(m, 0xFF0F, 5, (uint8_t)(0xE0u | m->interrupt_flags));
    }
    m->ppu_stat_line = (uint8_t)line;
}

/* MODEL: BOTH GATE-00 basis=diagnostics-only */
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

/* Model predicates are profile tests. They are the only way later code asks which console is
 * running, so a model difference is always visible as a guarded branch. */
/* MODEL: BOTH GATE-00 basis=profile-test */
static int model_is_dmg(const gbb_instance *m) { return m->profile == GBB_PROFILE_DMG_CPU_B; }

/* MODEL: BOTH GATE-00 basis=profile-test */
static int model_is_cgb(const gbb_instance *m) { return m->profile == GBB_PROFILE_CGB_CPU_E; }

/* Post-boot provenance table (D-06). Every value a profile starts with lives in one row, with
 * where the number came from. There are three columns: DMG (the DMG-CPU-B profile), CGB (the
 * CGB-CPU-E profile running a CGB-mode ROM) and COMPAT (the CGB-CPU-E profile running in DMG
 * compatibility mode, including with no ROM loaded, D-04). The DMG column records the value this
 * core implements, not necessarily Pan Docs: a cell that differs from Pan Docs says so in its
 * reason (diverges-from-pandocs) instead of being quietly "corrected", because the v0.1 DMG
 * baseline is byte-pinned (tests/test_cgb_postboot.c, tests/scripts/verify-dmg-baseline.sh).
 * Only COMPAT cells may carry HW_TEST, and only where a named Mooneye hardware test pins them;
 * no CGB-mode cell has a hardware oracle. */
typedef enum {
    PROV_HW_TEST = 1,
    PROV_PANDOCS,
    PROV_ORACLE_SAMEBOY,
    PROV_POLICY,
    PROV_HEADER_DERIVED
} post_boot_prov;

/* Numbered source list. */
typedef enum {
    SRC_NONE = 0,
    SRC_PANDOCS_POWER_UP = 1,   /* Pan Docs, Power Up Sequence */
    SRC_V01_POLICY_D025 = 2,    /* v0.1 DMG-CPU-B policy, DECISIONS D-025 */
    SRC_CART_HEADER = 3,        /* cartridge header byte $14D */
    SRC_MOONEYE_BOOT_REGS = 4,  /* Mooneye boot_regs-cgb (CPU registers, compat mode) */
    SRC_MOONEYE_BOOT_HWIO = 5,  /* Mooneye boot_hwio-C (I/O registers, compat mode) */
    SRC_MOONEYE_BOOT_DIV = 6,   /* Mooneye boot_div-cgbABCDE (DIV phase, compat mode) */
    SRC_SAMEBOY_ORACLE = 7,     /* SameBoy CGB boot state (differential oracle) */
    SRC_CGB_POLICY_D007 = 8     /* CGB-profile policy, phase 10 D-06 / D-07 */
} post_boot_source;

typedef enum {
    PB_A, PB_F, PB_B, PB_C, PB_D, PB_E, PB_H, PB_L, PB_SP, PB_PC,
    PB_DIV, PB_DIVIDER_COUNTER, PB_DIVIDER_PHASE,
    PB_TIMA, PB_TMA, PB_TAC,
    PB_SERIAL_DATA, PB_SERIAL_CONTROL,
    PB_IE, PB_IF, PB_IME,
    PB_NR11, PB_NR12, PB_CH1_ENABLED,
    PB_NR50, PB_NR51, PB_APU_POWER,
    PB_DMA_REGISTER,
    PB_LCDC, PB_STAT, PB_LY, PB_LYC, PB_SCX, PB_SCY, PB_WX, PB_WY,
    PB_BGP, PB_OBP0, PB_OBP1, PB_PPU_MODE,
    PB_JOYPAD_SELECT, PB_JOYPAD_BUTTONS,
    PB_KEY1, PB_VRAM_BANK, PB_SVBK, PB_WRAM_BANK, PB_BCPS, PB_OCPS,
    PB_FF72, PB_FF73, PB_FF74, PB_FF75,
    PB_BG_CRAM_FILL, PB_OBJ_CRAM_FILL, PB_OPRI,
    PB_RAM_FILL,
    PB_FIELD_COUNT
} post_boot_field;

typedef struct {
    uint16_t value;
    uint8_t prov;
    uint8_t src_id;
    const char *reason;
} post_boot_cell;

typedef struct {
    uint8_t field;
    post_boot_cell dmg;
    post_boot_cell cgb;    /* CGB-CPU-E running a CGB-mode ROM */
    post_boot_cell compat; /* CGB-CPU-E in DMG compatibility mode, or with no ROM (D-04) */
} post_boot_row;

#define PB_PD(v) { (v), PROV_PANDOCS, SRC_PANDOCS_POWER_UP, "Pan Docs Power Up Sequence, DMG" }
#define PB_DIVERGES(v, why) { (v), PROV_POLICY, SRC_V01_POLICY_D025, why }
#define PB_POLICY(v, why) { (v), PROV_POLICY, SRC_V01_POLICY_D025, why }
/* CGB-profile cells. A CGB-mode cell never claims HW_TEST (no hardware oracle covers CGB mode). */
#define PBC_PD(v) { (v), PROV_PANDOCS, SRC_PANDOCS_POWER_UP, "Pan Docs Power Up Sequence, CGB" }
#define PBC_POLICY(v, why) { (v), PROV_POLICY, SRC_CGB_POLICY_D007, why }
/* Compat-mode cells pinned by a named Mooneye hardware test. */
#define PBK_REGS(v) { (v), PROV_HW_TEST, SRC_MOONEYE_BOOT_REGS, "Mooneye boot_regs-cgb, compat mode" }
#define PBK_HWIO(v) { (v), PROV_HW_TEST, SRC_MOONEYE_BOOT_HWIO, "Mooneye boot_hwio-C, compat mode" }
#define PBK_PD(v) { (v), PROV_PANDOCS, SRC_PANDOCS_POWER_UP, "Pan Docs Power Up Sequence, CGB in compatibility mode" }

/* DMG-column cells of CGB-only registers: the profile does not decode them (D-09), so the value is
 * inert. The reason says so rather than inventing a hardware claim. */
#define PB_NA(v) { (v), PROV_POLICY, SRC_V01_POLICY_D025, "not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored)" }
#define PB_INIT0 "initial $00 per D-10; no hardware oracle for this CGB register"
#define PB_IDX_VERIFY "no hardware oracle for CGB-mode index"

#define PB_VARIES "no hardware oracle for CGB mode; real hardware varies with the header and held buttons"
#define PB_CRAM_COMPAT "the compat renderer never reads CRAM and the data ports read $FF in compat mode; deterministic fill only"
#define PB_SAME_AS_DMG "same value as the DMG cell; Pan Docs gives no CGB-specific value"
#define PB_CH1_SILENT "channel 1 enabled-but-silent: current volume 0, no boot chime is synthesised (A2)"

static const post_boot_row post_boot[PB_FIELD_COUNT] = {
    { PB_A,  PB_PD(0x01u), PBC_PD(0x11u), PBK_REGS(0x11u) },
    /* F is $B0 (H and C set) on the DMG profile when header byte $14D is non-zero, else $80; the
     * DMG cell holds the $80 base. On the CGB profile F is $80 regardless of the header checksum. */
    { PB_F,  { 0x80u, PROV_HEADER_DERIVED, SRC_CART_HEADER, "$B0 when header byte $14D is non-zero, else $80" },
             PBC_PD(0x80u), PBK_REGS(0x80u) },
    /* Compat B follows the licensee title-sum rule, so the compat cell holds the no-ROM value and
     * post_boot_apply derives the rest from the header. */
    { PB_B,  PB_PD(0x00u), PBC_PD(0x00u),
             { 0x00u, PROV_PANDOCS, SRC_PANDOCS_POWER_UP, "Pan Docs: B is the title-byte sum when the licensee is $01 (or $33 with new licensee \"01\"), else $00; header-derived" } },
    { PB_C,  PB_PD(0x13u), PBC_PD(0x00u), PBK_REGS(0x00u) },
    { PB_D,  PB_PD(0x00u), PBC_PD(0xFFu), PBK_REGS(0x00u) },
    { PB_E,  PB_PD(0xD8u), PBC_PD(0x56u), PBK_REGS(0x08u) },
    { PB_H,  PB_PD(0x01u), PBC_PD(0x00u), PBK_REGS(0x00u) },
    /* Compat L is $7C unless the title-sum rule selects HL = $991A; post_boot_apply derives that. */
    { PB_L,  PB_PD(0x4Du), PBC_PD(0x0Du), PBK_REGS(0x7Cu) },
    { PB_SP, PB_PD(0xFFFEu), PBC_PD(0xFFFEu), PBK_REGS(0xFFFEu) },
    { PB_PC, PB_PD(0x0100u), PBC_PD(0x0100u), PBK_PD(0x0100u) },
    { PB_DIV, PB_PD(0xABu), PBC_POLICY(0x26u, PB_VARIES),
              { 0x26u, PROV_HW_TEST, SRC_MOONEYE_BOOT_DIV, "Mooneye boot_div-cgbABCDE; applicability CGB A-E, not a CGB-E-only claim" } },
    { PB_DIVIDER_COUNTER, PB_POLICY(0xAB00u, "internal 16-bit counter whose high byte is DIV"),
              PBC_POLICY(0x2678u, PB_VARIES),
              { 0x2678u, PROV_HW_TEST, SRC_MOONEYE_BOOT_DIV, "Mooneye boot_div-cgbABCDE; applicability CGB A-E, not a CGB-E-only claim" } },
    { PB_DIVIDER_PHASE, PB_POLICY(0u, "sub-tick phase of the divider counter starts aligned"),
              PBC_POLICY(0u, PB_VARIES),
              { 0u, PROV_HW_TEST, SRC_MOONEYE_BOOT_DIV, "Mooneye boot_div-cgbABCDE; applicability CGB A-E, not a CGB-E-only claim" } },
    { PB_TIMA, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_TMA, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_TAC, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_SERIAL_DATA, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_SERIAL_CONTROL, PB_PD(0x7Eu), PBC_PD(0x7Fu), PBK_HWIO(0x7Eu) },
    { PB_IE, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_IF, PB_DIVERGES(0x00u, "diverges-from-pandocs: IF reads $E0 here; Pan Docs lists $E1"),
             PBC_PD(0x01u), PBK_HWIO(0x01u) },
    { PB_IME, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    /* Channel 1 is enabled at hand-off (NR52 $F1) but its current volume is 0, so it is silent. */
    { PB_NR11, PB_PD(0x00u), PBC_PD(0x80u), PBK_HWIO(0x80u) },
    { PB_NR12, PB_PD(0x00u), PBC_PD(0xF3u), PBK_HWIO(0xF3u) },
    { PB_CH1_ENABLED, PB_PD(0u), PBC_POLICY(1u, PB_CH1_SILENT),
                      { 1u, PROV_POLICY, SRC_CGB_POLICY_D007, PB_CH1_SILENT } },
    { PB_NR50, PB_DIVERGES(0x00u, "diverges-from-pandocs: NR50 is 0 here; Pan Docs lists $77"),
               PBC_PD(0x77u), PBK_HWIO(0x77u) },
    { PB_NR51, PB_DIVERGES(0xFFu, "diverges-from-pandocs: NR51 is $FF here; Pan Docs lists $F3"),
               PBC_PD(0xF3u), PBK_HWIO(0xF3u) },
    { PB_APU_POWER, PB_DIVERGES(1u, "diverges-from-pandocs: NR52 reads $F0 here; Pan Docs lists $F1 (channel 1 on)"),
                    PBC_PD(1u), PBK_HWIO(1u) },
    { PB_DMA_REGISTER, PB_PD(0xFFu), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_LCDC, PB_PD(0x91u), PBC_PD(0x91u), PBK_PD(0x91u) },
    { PB_STAT, PB_DIVERGES(0x00u, "diverges-from-pandocs: stored STAT bits are 0 and the mode/LY below make STAT read $86; Pan Docs lists $85"),
               PBC_POLICY(0x00u, PB_VARIES), PBC_POLICY(0x00u, PB_VARIES) },
    { PB_LY, PB_PD(0x00u), PBC_POLICY(0x00u, PB_VARIES), PBC_POLICY(0x00u, PB_VARIES) },
    { PB_LYC, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_SCX, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_SCY, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_WX, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_WY, PB_PD(0x00u), PBC_PD(0x00u), PBK_PD(0x00u) },
    { PB_BGP, PB_PD(0xFCu), PBC_PD(0xFCu), PBK_PD(0xFCu) },
    { PB_OBP0, PB_DIVERGES(0xFFu, "diverges-from-pandocs: OBP0 is $FF here; Pan Docs does not give a fixed value"),
               PBC_POLICY(0xFFu, PB_SAME_AS_DMG), PBC_POLICY(0xFFu, PB_SAME_AS_DMG) },
    { PB_OBP1, PB_DIVERGES(0xFFu, "diverges-from-pandocs: OBP1 is $FF here; Pan Docs does not give a fixed value"),
               PBC_POLICY(0xFFu, PB_SAME_AS_DMG), PBC_POLICY(0xFFu, PB_SAME_AS_DMG) },
    { PB_PPU_MODE, PB_DIVERGES(2u, "diverges-from-pandocs: starts in mode 2 at line 0; Pan Docs STAT $85 implies vblank"),
                   PBC_POLICY(2u, PB_VARIES), PBC_POLICY(2u, PB_VARIES) },
    /* P1 reads $FF (select lines $30, no buttons) where Pan Docs lists $CF. */
    { PB_JOYPAD_SELECT, PB_DIVERGES(0x30u, "diverges-from-pandocs: P1 reads $FF here; Pan Docs lists $CF"),
                        { 0x30u, PROV_ORACLE_SAMEBOY, SRC_SAMEBOY_ORACLE, "SameBoy CGB boot state: P1 reads $FF" },
                        PBK_HWIO(0x30u) },
    { PB_JOYPAD_BUTTONS, PB_POLICY(0u, "no button held at power-on"),
                         PBC_POLICY(0u, "no button held at power-on"), PBC_POLICY(0u, "no button held at power-on") },
    /* KEY1 bit 0 is the armed flag; no speed switch is built, so it stays 0 until written. */
    { PB_KEY1, PB_NA(0u), PBC_PD(0u), PBK_PD(0u) },
    { PB_VRAM_BANK, PB_POLICY(0u, "the DMG profile pins the VRAM bank at 0"), PBC_PD(0u), PBK_PD(0u) },
    { PB_SVBK, PB_NA(0u), PBC_PD(0u), PBK_PD(0u) },
    { PB_WRAM_BANK, PB_POLICY(1u, "the DMG profile pins the switchable WRAM bank at 1"), PBC_PD(1u), PBK_PD(1u) },
    /* BCPS and OCPS: unused bit 6 reads 1. Compat-mode values are pinned by Mooneye boot_hwio-C;
     * the CGB-mode index has no oracle. */
    { PB_BCPS, PB_NA(0u), PBC_POLICY(0xC0u, PB_IDX_VERIFY), PBK_HWIO(0xC8u) },
    { PB_OCPS, PB_NA(0u), PBC_POLICY(0xC0u, PB_IDX_VERIFY), PBK_HWIO(0xD0u) },
    { PB_FF72, PB_NA(0u), PBC_POLICY(0u, PB_INIT0), PBC_POLICY(0u, PB_INIT0) },
    { PB_FF73, PB_NA(0u), PBC_POLICY(0u, PB_INIT0), PBC_POLICY(0u, PB_INIT0) },
    { PB_FF74, PB_NA(0u), PBC_POLICY(0u, PB_INIT0), PBC_POLICY(0u, "compat mode does not decode FF74: reads $FF, writes ignored; stored value stays 0") },
    { PB_FF75, PB_NA(0u), PBC_POLICY(0u, "bits 4-6 stored; reads $8F with them clear"), PBC_POLICY(0u, "bits 4-6 stored; reads $8F with them clear") },
    /* Palette RAM fill word (D-14): every colour of the side is this RGB555 value, low byte first.
     * The compat renderer never reads CRAM and its data ports read $FF, so that column is a
     * deterministic fill only. OPRI is stored but has no priority effect after boot (D-08). */
    { PB_BG_CRAM_FILL, PB_NA(0u), PBC_PD(0x7FFFu), PBC_POLICY(0x7FFFu, PB_CRAM_COMPAT) },
    { PB_OBJ_CRAM_FILL, PB_NA(0u), PBC_POLICY(0x7FFFu, "Pan Docs calls OBJ CRAM uninitialised; white by policy (D-14)"),
                        PBC_POLICY(0x7FFFu, PB_CRAM_COMPAT) },
    { PB_OPRI, PB_NA(0u), PBC_POLICY(0u, "boot ROM leaves priority by OAM index; no hardware oracle (D-08)"),
               PBC_POLICY(0u, "compat mode reads OPRI as $FF; stored value inert") },
    { PB_RAM_FILL, PB_POLICY(0u, "D-025 deterministic fill"),
                   PBC_POLICY(0u, "D-025 deterministic fill"), PBC_POLICY(0u, "D-025 deterministic fill") },
};

_Static_assert(sizeof(post_boot) / sizeof(post_boot[0]) == PB_FIELD_COUNT,
               "post_boot[] must have one row per post_boot_field");

/* The column a profile and execution mode select (D-06). The no-ROM state of a CGB instance is
 * the compatibility column (D-04). */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static const post_boot_cell *post_boot_column(const gbb_instance *m, const post_boot_row *row) {
    if (model_is_dmg(m)) return &row->dmg;
    if (m->exec_mode == GBB_MODE_CGB) return &row->cgb;
    return &row->compat;
}

/* Compat-mode B and HL follow the licensee title-sum rule (Pan Docs): when the old licensee byte
 * $14B is $01, or $33 with new licensee "01" at $144-$145, B is the 8-bit sum of the title bytes
 * $134-$143 and HL is $991A if that sum is $43 or $58. Otherwise B is $00 and HL is $007C. */
/* MODEL: CGB_ONLY GATE-68 GUARD=model_is_cgb -- compat-mode B and HL are derived from the licensee title sum */
static void compat_title_registers(const gbb_instance *m, uint8_t *b, uint16_t *hl) {
    *b = 0u;
    *hl = 0x007Cu;
    if (!model_is_cgb(m) || m->rom == NULL || m->rom_size <= 0x14Cu) return;
    const uint8_t old_licensee = m->rom[0x14Bu];
    const int new_licensee_01 = m->rom[0x144u] == (uint8_t)'0' && m->rom[0x145u] == (uint8_t)'1';
    if (old_licensee != 0x01u && !(old_licensee == 0x33u && new_licensee_01)) return;
    uint8_t sum = 0u;
    for (unsigned i = 0x134u; i <= 0x143u; ++i) sum = (uint8_t)(sum + m->rom[i]);
    *b = sum;
    if (sum == 0x43u || sum == 0x58u) *hl = 0x991Au;
}

/* Assign every table-backed field. Rows are indexed by field, so each field is set exactly once;
 * the switch has no default so the compiler flags a field added to the enum but not handled. */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void post_boot_apply(gbb_instance *m) {
    const int compat_column = model_is_cgb(m) && m->exec_mode != GBB_MODE_CGB;
    uint8_t title_b = 0u;
    uint16_t title_hl = 0x007Cu;
    if (compat_column) compat_title_registers(m, &title_b, &title_hl);
    for (unsigned i = 0; i < PB_FIELD_COUNT; ++i) {
        const post_boot_cell *c = post_boot_column(m, &post_boot[i]);
        const uint8_t v = (uint8_t)c->value;
        switch ((post_boot_field)post_boot[i].field) {
        case PB_A: m->a = v; break;
        case PB_F: {
            /* MODEL: DMG_ONLY GATE-03 GUARD=model_is_dmg -- the header-checksum F branch exists on the DMG profile only; CGB F is $80 */
            const int checksum_nonzero = model_is_dmg(m) && m->rom != NULL && m->rom_size > 0x14Du &&
                                         m->rom[0x14Du] != 0;
            m->f = checksum_nonzero ? (uint8_t)(v | 0x30u) : v;
            break;
        }
        case PB_B: m->b = compat_column ? title_b : v; break;
        case PB_C: m->c = v; break;
        case PB_D: m->d = v; break;
        case PB_E: m->e = v; break;
        case PB_H: m->h = compat_column ? (uint8_t)(title_hl >> 8) : v; break;
        case PB_L: m->l = compat_column ? (uint8_t)title_hl : v; break;
        case PB_SP: m->sp = c->value; break;
        case PB_PC: m->pc = c->value; break;
        case PB_DIV:
            /* MODEL: BOTH GATE-04 basis="post_boot[] column per profile (D-06)" -- post-boot DIV differs by model */
            m->div = v; break;
        case PB_DIVIDER_COUNTER: m->divider_counter = c->value; break;
        case PB_DIVIDER_PHASE: m->divider_phase = v; break;
        case PB_TIMA: m->tima = v; break;
        case PB_TMA: m->tma = v; break;
        case PB_TAC: m->tac = v; break;
        case PB_SERIAL_DATA: m->serial_data = v; break;
        case PB_SERIAL_CONTROL:
            /* MODEL: BOTH GATE-05 basis="post_boot[] column per profile (D-06)" -- post-boot SC differs by model */
            m->serial_control = v; break;
        case PB_IE: m->ie = v; break;
        case PB_IF:
            /* MODEL: BOTH GATE-06 basis="post_boot[] column per profile (D-06)" -- post-boot IF differs by model */
            m->interrupt_flags = v; break;
        case PB_IME: m->ime = v; break;
        case PB_NR11: m->apu_pulse[0].duty_length = v; break;
        case PB_NR12: m->apu_pulse[0].envelope = v; break;
        case PB_CH1_ENABLED:
            /* Enabled with current volume 0 (the zeroed pulse state): NR52 reports channel 1 on but
             * the mixer produces no sample, and no boot chime is synthesised. The frequency and
             * timer are a valid idle state; the length counter is the value NR11 would load. */
            if (v != 0u) {
                apu_pulse_channel *p = &m->apu_pulse[0];
                p->enabled = 1;
                p->length = (uint16_t)(64u - (p->duty_length & 0x3Fu));
                p->frequency = 0x7FFu;
                p->frequency_low = 0xFFu;
                p->timer = (uint16_t)((2048u - p->frequency) * 64u);
                p->envelope_timer = (uint8_t)((p->envelope & 7u) == 0u ? 8u : p->envelope & 7u);
            }
            break;
        case PB_NR50:
            /* MODEL: BOTH GATE-07 basis="post_boot[] column per profile (D-06)" -- post-boot APU register literals differ by model */
            m->apu_nr50 = v; break;
        case PB_NR51: m->apu_nr51 = v; break;
        case PB_APU_POWER: m->apu_power = v; break;
        case PB_DMA_REGISTER:
            /* MODEL: BOTH GATE-08 basis="post_boot[] column per profile (D-06)" -- post-boot DMA register differs by model */
            m->dma_register = v; break;
        case PB_LCDC:
            /* MODEL: BOTH GATE-11 basis=PANDOCS -- LCDC, BGP and OBP post-boot values are common to both models */
            m->lcdc = v; break;
        case PB_STAT: m->stat = v; break;
        case PB_LY: m->ly = v; break;
        case PB_LYC: m->lyc = v; break;
        case PB_SCX: m->scx = v; break;
        case PB_SCY: m->scy = v; break;
        case PB_WX: m->wx = v; break;
        case PB_WY: m->wy = v; break;
        case PB_BGP: m->bgp = v; break;
        case PB_OBP0: m->obp0 = v; break;
        case PB_OBP1: m->obp1 = v; break;
        case PB_PPU_MODE:
            /* MODEL: UNKNOWN GATE-10 research:14 -- post-boot PPU mode, LY and STAT literals differ by model; the CGB mode-3 and line-0 timing question is deferred by D-09/D-12 */
            m->ppu_mode = v; break;
        case PB_JOYPAD_SELECT: m->joypad_select = v; break;
        case PB_JOYPAD_BUTTONS: m->joypad_buttons = v; break;
        case PB_KEY1: m->key1_armed = v; break;
        case PB_VRAM_BANK: m->vram_bank = v; break;
        case PB_SVBK: m->svbk = v; break;
        case PB_WRAM_BANK: m->wram_bank = v; break;
        case PB_BCPS: m->bcps = v; break;
        case PB_OCPS: m->ocps = v; break;
        case PB_FF72: m->ff72 = v; break;
        case PB_FF73: m->ff73 = v; break;
        case PB_FF74: m->ff74 = v; break;
        case PB_FF75: m->ff75 = v; break;
        case PB_BG_CRAM_FILL:
        case PB_OBJ_CRAM_FILL: {
            /* MODEL: BOTH GATE-00 basis="post_boot[] column per profile (D-06)" -- palette RAM fill; the DMG column is inert and never read */
            uint8_t *cram = post_boot[i].field == PB_BG_CRAM_FILL ? m->bg_cram : m->obj_cram;
            for (unsigned word = 0; word < sizeof(m->bg_cram) / 2u; ++word) {
                cram[word * 2u] = (uint8_t)c->value;
                cram[word * 2u + 1u] = (uint8_t)(c->value >> 8);
            }
            break;
        }
        case PB_OPRI: m->opri = (uint8_t)(v & 1u); break;
        case PB_RAM_FILL:
            /* MODEL: BOTH GATE-09 basis=D-025 -- RAM fill is emulator policy; hardware power-on RAM is unspecified */
            memset(m->wram, v, sizeof(m->wram));
            memset(m->hram, v, sizeof(m->hram));
            memset(m->vram, v, sizeof(m->vram));
            memset(m->oam, v, sizeof(m->oam));
            break;
        case PB_FIELD_COUNT: break;
        }
    }
}

/* Work RAM is two fixed 4 KiB halves: C000-CFFF (and its echo E000-EFFF) is always bank 0, and
 * D000-DFFF (echo F000-FDFF) is wram[wram_bank]. Masking to 13 bits folds the echo onto the main
 * range. DMG pins wram_bank to 1, so the two halves are contiguous there and no profile branch is
 * needed on the access path. Callers pass only C000-FDFF. */
/* MODEL: BOTH GATE-00 basis="DMG pins wram_bank=1 and vram_bank=0" */
static const uint8_t *wram_byte(const gbb_instance *m, uint16_t address) {
    unsigned offset = (unsigned)address & 0x1FFFu;
    unsigned bank = offset < GBB_WRAM_BANK_SIZE ? 0u : m->wram_bank;
    return &m->wram[bank][offset & (GBB_WRAM_BANK_SIZE - 1u)];
}

/* MODEL: BOTH GATE-00 basis="DMG pins wram_bank=1 and vram_bank=0" */
static uint8_t *wram_byte_mut(gbb_instance *m, uint16_t address) {
    return (uint8_t *)wram_byte(m, address);
}

/* Register visibility (D-06, D-09, D-10). One row per address FF00-FF7F with a DMG, CGB-mode and
 * CGB-compat column. Rows for addresses the pre-CGB code in read8/write8 already handles are
 * EXISTING and are not decoded here. The DMG column of FF4C-FF7F is DMG_STOP: the DMG profile never
 * enters io_read_cgb/io_write_cgb, so reads there still stop and writes stay silent no-ops (C4).
 * A DEFERRED cell belongs to a later phase: its reads stop through read_supported before anything
 * changes, and its writes latch bus_unsupported and are dropped, so a guest never sees an invented
 * value (OQ5). Sources: IOS_PANDOCS (Pan Docs), IOS_HW_TEST (Mooneye boot_hwio-C / unused_hwio-C),
 * IOS_SAMEBOY (SameBoy oracle), IOS_POLICY (project choice). */
typedef enum {
    IO_UNSET = 0,     /* zero-initialised hole: a row missing from the table */
    IO_EXISTING,      /* handled by the pre-CGB read8/write8 chain */
    IO_DMG_STOP,      /* DMG only: reads stop UNSUPPORTED_BUS, writes are ignored */
    IO_CONST_FF,      /* reads $FF, writes ignored */
    IO_KEY1,
    IO_VBK,
    IO_SVBK,
    IO_STORE,         /* stored byte: reads (stored | read_or), writes keep (value & write_mask) */
    IO_DEFERRED_RW,   /* read stops, write latches and is dropped */
    IO_DEFERRED_W,    /* reads $FF, write latches and is dropped */
    IO_BCPD,          /* background palette data port (appended: IO_UNSET stays 0) */
    IO_OCPD,          /* object palette data port */
    IO_OPRI,          /* object priority mode: bit 0 stored, no effect after boot */
    IO_PCM12,         /* PCM12: channel 2:channel 1 digital DAC values */
    IO_PCM34          /* PCM34: channel 4:channel 3 digital DAC values */
} io_kind;

typedef enum { IOS_NONE = 0, IOS_PANDOCS, IOS_HW_TEST, IOS_SAMEBOY, IOS_POLICY, IOS_EXISTING } io_source;

typedef struct {
    uint8_t kind;
    uint8_t phase;       /* owning phase of a DEFERRED cell */
    uint8_t read_or;     /* STORE: bits that always read 1 */
    uint8_t write_mask;  /* STORE: bits that are stored */
} io_cell;

typedef struct {
    io_cell dmg, cgb, compat;
    uint8_t src;
} io_row;

#define IOC(k) { IO_##k, 0, 0, 0 }
#define IOC_DEF(k, ph) { IO_##k, (ph), 0, 0 }
#define IOC_ST(or_bits, wmask) { IO_STORE, 0, (or_bits), (wmask) }
#define IO_EXISTING_ROW { IOC(EXISTING), IOC(EXISTING), IOC(EXISTING), IOS_EXISTING }
#define IO_UNUSED_ROW { IOC(DMG_STOP), IOC(CONST_FF), IOC(CONST_FF), IOS_HW_TEST }

#define IO_VISIBILITY_ROWS 0x80u
static const io_row io_visibility[IO_VISIBILITY_ROWS] = {
    [0x00] = IO_EXISTING_ROW,
    [0x01] = IO_EXISTING_ROW,
    [0x02] = IO_EXISTING_ROW,
    [0x03] = IO_UNUSED_ROW,
    [0x04] = IO_EXISTING_ROW,
    [0x05] = IO_EXISTING_ROW,
    [0x06] = IO_EXISTING_ROW,
    [0x07] = IO_EXISTING_ROW,
    [0x08] = IO_UNUSED_ROW,
    [0x09] = IO_UNUSED_ROW,
    [0x0A] = IO_UNUSED_ROW,
    [0x0B] = IO_UNUSED_ROW,
    [0x0C] = IO_UNUSED_ROW,
    [0x0D] = IO_UNUSED_ROW,
    [0x0E] = IO_UNUSED_ROW,
    [0x0F] = IO_EXISTING_ROW,
    [0x10] = IO_EXISTING_ROW,
    [0x11] = IO_EXISTING_ROW,
    [0x12] = IO_EXISTING_ROW,
    [0x13] = IO_EXISTING_ROW,
    [0x14] = IO_EXISTING_ROW,
    [0x15] = IO_UNUSED_ROW,
    [0x16] = IO_EXISTING_ROW,
    [0x17] = IO_EXISTING_ROW,
    [0x18] = IO_EXISTING_ROW,
    [0x19] = IO_EXISTING_ROW,
    [0x1A] = IO_EXISTING_ROW,
    [0x1B] = IO_EXISTING_ROW,
    [0x1C] = IO_EXISTING_ROW,
    [0x1D] = IO_EXISTING_ROW,
    [0x1E] = IO_EXISTING_ROW,
    [0x1F] = IO_UNUSED_ROW,
    [0x20] = IO_EXISTING_ROW,
    [0x21] = IO_EXISTING_ROW,
    [0x22] = IO_EXISTING_ROW,
    [0x23] = IO_EXISTING_ROW,
    [0x24] = IO_EXISTING_ROW,
    [0x25] = IO_EXISTING_ROW,
    [0x26] = IO_EXISTING_ROW,
    [0x27] = IO_UNUSED_ROW,
    [0x28] = IO_UNUSED_ROW,
    [0x29] = IO_UNUSED_ROW,
    [0x2A] = IO_UNUSED_ROW,
    [0x2B] = IO_UNUSED_ROW,
    [0x2C] = IO_UNUSED_ROW,
    [0x2D] = IO_UNUSED_ROW,
    [0x2E] = IO_UNUSED_ROW,
    [0x2F] = IO_UNUSED_ROW,
    [0x30] = IO_EXISTING_ROW,
    [0x31] = IO_EXISTING_ROW,
    [0x32] = IO_EXISTING_ROW,
    [0x33] = IO_EXISTING_ROW,
    [0x34] = IO_EXISTING_ROW,
    [0x35] = IO_EXISTING_ROW,
    [0x36] = IO_EXISTING_ROW,
    [0x37] = IO_EXISTING_ROW,
    [0x38] = IO_EXISTING_ROW,
    [0x39] = IO_EXISTING_ROW,
    [0x3A] = IO_EXISTING_ROW,
    [0x3B] = IO_EXISTING_ROW,
    [0x3C] = IO_EXISTING_ROW,
    [0x3D] = IO_EXISTING_ROW,
    [0x3E] = IO_EXISTING_ROW,
    [0x3F] = IO_EXISTING_ROW,
    [0x40] = IO_EXISTING_ROW,
    [0x41] = IO_EXISTING_ROW,
    [0x42] = IO_EXISTING_ROW,
    [0x43] = IO_EXISTING_ROW,
    [0x44] = IO_EXISTING_ROW,
    [0x45] = IO_EXISTING_ROW,
    [0x46] = IO_EXISTING_ROW,
    [0x47] = IO_EXISTING_ROW,
    [0x48] = IO_EXISTING_ROW,
    [0x49] = IO_EXISTING_ROW,
    [0x4A] = IO_EXISTING_ROW,
    [0x4B] = IO_EXISTING_ROW,
    [0x4C] = { IOC(DMG_STOP), IOC(CONST_FF), IOC(CONST_FF), IOS_PANDOCS }, /* KEY0: CPU mode register, locked after boot; reads $FF, writes ignored */
    [0x4D] = { IOC(DMG_STOP), IOC(KEY1), IOC(CONST_FF), IOS_PANDOCS }, /* KEY1: speed switch; bit 7 reports speed and bit 0 arms it */
    [0x4E] = IO_UNUSED_ROW,
    [0x4F] = { IOC(DMG_STOP), IOC(VBK), IOC(VBK), IOS_PANDOCS }, /* VBK: VRAM bank; bit 0 selects the bank in CGB mode only */
    [0x50] = IO_UNUSED_ROW,
    [0x51] = { IOC(DMG_STOP), IOC_ST(0xFF, 0xFF), IOC(CONST_FF), IOS_POLICY }, /* FF51: private source high latch, read mask keeps $FF */
    [0x52] = { IOC(DMG_STOP), IOC_ST(0xFF, 0xF0), IOC(CONST_FF), IOS_POLICY }, /* FF52: private source low latch, read mask keeps $FF */
    [0x53] = { IOC(DMG_STOP), IOC_ST(0xFF, 0x1F), IOC(CONST_FF), IOS_POLICY }, /* FF53: private destination high latch */
    [0x54] = { IOC(DMG_STOP), IOC_ST(0xFF, 0xF0), IOC(CONST_FF), IOS_POLICY }, /* FF54: private destination low latch */
    [0x55] = { IOC(DMG_STOP), IOC_ST(0x00, 0xFF), IOC(CONST_FF), IOS_POLICY }, /* FF55: bounded HBlank control/status */
    [0x56] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 14), IOC(CONST_FF), IOS_PANDOCS }, /* RP infrared port: deferred to phase 14 */
    [0x57] = IO_UNUSED_ROW,
    [0x58] = IO_UNUSED_ROW,
    [0x59] = IO_UNUSED_ROW,
    [0x5A] = IO_UNUSED_ROW,
    [0x5B] = IO_UNUSED_ROW,
    [0x5C] = IO_UNUSED_ROW,
    [0x5D] = IO_UNUSED_ROW,
    [0x5E] = IO_UNUSED_ROW,
    [0x5F] = IO_UNUSED_ROW,
    [0x60] = IO_UNUSED_ROW,
    [0x61] = IO_UNUSED_ROW,
    [0x62] = IO_UNUSED_ROW,
    [0x63] = IO_UNUSED_ROW,
    [0x64] = IO_UNUSED_ROW,
    [0x65] = IO_UNUSED_ROW,
    [0x66] = IO_UNUSED_ROW,
    [0x67] = IO_UNUSED_ROW,
    [0x68] = { IOC(DMG_STOP), IOC_ST(0x40, 0xBF), IOC_ST(0x40, 0xBF), IOS_HW_TEST }, /* BCPS: background palette index; unused bit 6 reads 1 */
    [0x69] = { IOC(DMG_STOP), IOC(BCPD), IOC(CONST_FF), IOS_PANDOCS }, /* BCPD: background palette data; auto-increment on write even when blocked, reads never increment; compat mode ignores it without increment */
    [0x6A] = { IOC(DMG_STOP), IOC_ST(0x40, 0xBF), IOC_ST(0x40, 0xBF), IOS_HW_TEST }, /* OCPS: object palette index; unused bit 6 reads 1 */
    [0x6B] = { IOC(DMG_STOP), IOC(OCPD), IOC(CONST_FF), IOS_PANDOCS }, /* OCPD: object palette data; same port rules as BCPD; compat mode ignores it without increment */
    [0x6C] = { IOC(DMG_STOP), IOC(OPRI), IOC(CONST_FF), IOS_SAMEBOY }, /* OPRI: bit 0 stored and read back as $FE|bit0 in CGB mode; no effect on priority after boot (SameBoy memory.c; Pan Docs 'no effect ... after the boot ROM has been unmapped', TO BE VERIFIED); UNKNOWN */
    [0x6D] = IO_UNUSED_ROW,
    [0x6E] = IO_UNUSED_ROW,
    [0x6F] = IO_UNUSED_ROW,
    [0x70] = { IOC(DMG_STOP), IOC(SVBK), IOC(CONST_FF), IOS_PANDOCS }, /* SVBK: WRAM bank; raw 3 bits read back, 0 selects bank 1 */
    [0x71] = IO_UNUSED_ROW,
    [0x72] = { IOC(DMG_STOP), IOC_ST(0x00, 0xFF), IOC_ST(0x00, 0xFF), IOS_SAMEBOY }, /* FF72: undocumented CGB register, fully read/write */
    [0x73] = { IOC(DMG_STOP), IOC_ST(0x00, 0xFF), IOC_ST(0x00, 0xFF), IOS_SAMEBOY }, /* FF73: undocumented CGB register, fully read/write */
    [0x74] = { IOC(DMG_STOP), IOC_ST(0x00, 0xFF), IOC(CONST_FF), IOS_SAMEBOY }, /* FF74: undocumented CGB register; compat mode locks it */
    [0x75] = { IOC(DMG_STOP), IOC_ST(0x8F, 0x70), IOC_ST(0x8F, 0x70), IOS_PANDOCS }, /* FF75: only bits 4-6 are stored; the rest read 1 */
    [0x76] = { IOC(DMG_STOP), IOC(PCM12), IOC(CONST_FF), IOS_PANDOCS }, /* PCM12: channel 2:channel 1 digital output; compatibility mode locks it */
    [0x77] = { IOC(DMG_STOP), IOC(PCM34), IOC(CONST_FF), IOS_PANDOCS }, /* PCM34: channel 4:channel 3 digital output; compatibility mode locks it */
    [0x78] = IO_UNUSED_ROW,
    [0x79] = IO_UNUSED_ROW,
    [0x7A] = IO_UNUSED_ROW,
    [0x7B] = IO_UNUSED_ROW,
    [0x7C] = IO_UNUSED_ROW,
    [0x7D] = IO_UNUSED_ROW,
    [0x7E] = IO_UNUSED_ROW,
    [0x7F] = IO_UNUSED_ROW,
};

/* The cell the profile and execution mode select. Callers pass FF00-FF7F on the CGB profile. */
/* MODEL: CGB_ONLY GATE-69 GUARD=model_is_cgb -- the CGB register decode is never reached on the DMG profile */
static const io_cell *io_cgb_cell(const gbb_instance *m, uint16_t address) {
    const io_row *row = &io_visibility[address - 0xFF00u];
    if (!model_is_cgb(m)) return &row->dmg;
    return m->exec_mode == GBB_MODE_CGB ? &row->cgb : &row->compat;
}

/* CPU access locks for the PPU-owned memories. CRAM has its own predicate (D-12). */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int cpu_vram_access_allowed(const gbb_instance *m) {
    /* MODEL: UNKNOWN GATE-13 research:14 -- VRAM CPU lock window during mode 3; CGB lock-edge offsets are unresearched and deferred by D-09/D-12 */
    return (m->lcdc & 0x80u) == 0 || m->ppu_mode != 3u;
}

/* CRAM CPU lock. SameBoy's edge offsets and the black-pixel quirk are not modelled (D-12). */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int cpu_cram_access_allowed(const gbb_instance *m) {
    /* MODEL: UNKNOWN GATE-76 research:14 -- CRAM CPU lock is a plain mode-3 predicate; edge offsets unresearched (D-12) */
    return (m->lcdc & 0x80u) == 0 || m->ppu_mode != 3u;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int cpu_oam_access_allowed(const gbb_instance *m) {
    /* MODEL: UNKNOWN GATE-14 research:14 -- OAM CPU lock window during modes 2 and 3; CGB lock-edge offsets are unresearched and deferred by D-09/D-12 */
    return (m->lcdc & 0x80u) == 0 || m->ppu_mode == 0u || m->ppu_mode == 1u;
}

/* Palette data port write (D-11). The index register keeps bit 7 (auto-increment) and bit 6 reads 1
 * through the STORE mask on BCPS/OCPS; here only bits 0-5 address the 64-byte array. The index
 * advances after every write while bit 7 is set, even a write the mode-3 lock blocked, and it wraps
 * 63 to 0 inside bits 0-5 so no index bit leaks into bit 6. */
/* MODEL: BOTH GATE-00 basis=cgb-only-callers */
static void cram_data_write(uint8_t *index_reg, uint8_t cram[64], uint8_t value, int allowed) {
    const unsigned idx = (unsigned)*index_reg & 0x3Fu;
    if (allowed) cram[idx] = value;
    if ((*index_reg & 0x80u) != 0u) *index_reg = (uint8_t)(0x80u | ((idx + 1u) & 0x3Fu));
}

/* Palette data port read (D-11): the stored byte, or $FF while the lock blocks it. Never touches
 * the index register. */
/* MODEL: BOTH GATE-00 basis=cgb-only-callers */
static uint8_t cram_data_read(uint8_t index_reg, const uint8_t cram[64], int allowed) {
    return allowed ? cram[(unsigned)index_reg & 0x3Fu] : 0xFFu;
}

/* Storage behind a STORE cell. */
/* MODEL: BOTH GATE-00 basis="CGB-only storage selected by address" */
static const uint8_t *io_store_ptr(const gbb_instance *m, uint16_t address) {
    switch (address) {
    case 0xFF51: return &m->hdma.source_high;
    case 0xFF52: return &m->hdma.source_low;
    case 0xFF53: return &m->hdma.destination_high;
    case 0xFF54: return &m->hdma.destination_low;
    case 0xFF55: return &m->hdma.control_readback;
    case 0xFF68: return &m->bcps;
    case 0xFF6A: return &m->ocps;
    case 0xFF72: return &m->ff72;
    case 0xFF73: return &m->ff73;
    case 0xFF74: return &m->ff74;
    case 0xFF75: return &m->ff75;
    default: return NULL;
    }
}

static void hdma_register_write(gbb_instance *m, uint16_t address, uint8_t value);

/* Read FF4C-FF7F on the CGB profile. */
/* MODEL: CGB_ONLY GATE-70 GUARD=model_is_cgb -- CGB register reads */
static uint8_t io_read_cgb(const gbb_instance *m, uint16_t address) {
    if (!model_is_cgb(m)) return 0xFFu;
    const io_cell *c = io_cgb_cell(m, address);
    switch (c->kind) {
    case IO_KEY1: return (uint8_t)(0x7Eu | ((m->double_speed & 1u) << 7) | (m->key1_armed & 1u));
    case IO_VBK: return (uint8_t)(0xFEu | (m->vram_bank & 1u));
    case IO_SVBK: return (uint8_t)(0xF8u | (m->svbk & 7u));
    case IO_STORE: {
        const uint8_t *p = io_store_ptr(m, address);
        return p == NULL ? 0xFFu : (uint8_t)(*p | c->read_or);
    }
    case IO_BCPD: return cram_data_read(m->bcps, m->bg_cram, cpu_cram_access_allowed(m));
    case IO_OCPD: return cram_data_read(m->ocps, m->obj_cram, cpu_cram_access_allowed(m));
    case IO_OPRI: return (uint8_t)(0xFEu | (m->opri & 1u));
    case IO_PCM12:
    case IO_PCM34: return apu_pcm_read(m, address);
    default: return 0xFFu; /* CONST_FF, DEFERRED_W; DEFERRED_RW is refused before the read */
    }
}

/* Write FF4C-FF7F on the CGB profile. */
/* MODEL: CGB_ONLY GATE-71 GUARD=model_is_cgb -- CGB register writes */
static void io_write_cgb(gbb_instance *m, uint16_t address, uint8_t value) {
    if (!model_is_cgb(m)) return;
    if (address == 0xFF4Cu) return; /* D-03: KEY0 never changes speed or mode. P12-M32 */
    const io_cell *c = io_cgb_cell(m, address);
    switch (c->kind) {
    case IO_KEY1: m->key1_armed = (uint8_t)(value & 1u); break;
    case IO_VBK:
        /* Compatibility mode keeps the bank at 0: a DMG ROM cannot reach VRAM bank 1. */
        if (m->exec_mode == GBB_MODE_CGB) m->vram_bank = (uint8_t)(value & 1u);
        break;
    case IO_SVBK:
        m->svbk = (uint8_t)(value & 7u);
        m->wram_bank = m->svbk != 0u ? m->svbk : 1u;
        break;
    case IO_STORE: {
        if (address >= 0xFF51u && address <= 0xFF55u) {
            hdma_register_write(m, address, value);
            break;
        }
        uint8_t *p = (uint8_t *)io_store_ptr(m, address); /* m is mutable here */
        if (p != NULL) *p = (uint8_t)(value & c->write_mask);
        break;
    }
    case IO_BCPD: cram_data_write(&m->bcps, m->bg_cram, value, cpu_cram_access_allowed(m)); break;
    case IO_OCPD: cram_data_write(&m->ocps, m->obj_cram, value, cpu_cram_access_allowed(m)); break;
    case IO_OPRI:
        /* MODEL: UNKNOWN GATE-77 research:14 -- OPRI is stored without priority effect after boot (D-08) */
        m->opri = (uint8_t)(value & 1u);
        break;
    case IO_PCM12:
    case IO_PCM34:
#if GBB_TEST_CGB_PCM_WRITABLE
        {
            const unsigned index = address == 0xFF76u ? 0u : 1u;
            m->apu_pcm_test_override[index] = value;
            m->apu_pcm_test_override_valid |= (uint8_t)(1u << index);
        }
#endif
        break;
    case IO_DEFERRED_RW:
    case IO_DEFERRED_W:
        m->bus_unsupported = 1;
        m->bus_unsupported_address = address;
        break;
    default: break;
    }
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void reset_state(gbb_instance *m) {
    cart_reset_registers(&m->cart);
    /* APU channel state is cleared first: the post-boot table then sets channel 1 on the CGB
     * columns. The DMG column leaves it zero, as before. */
    memset(m->apu_pulse, 0, sizeof(m->apu_pulse));
    memset(&m->apu_wave, 0, sizeof(m->apu_wave));
    memset(&m->apu_noise, 0, sizeof(m->apu_noise));
#if GBB_TEST_CGB_PCM_WRITABLE
    memset(m->apu_pcm_test_override, 0, sizeof(m->apu_pcm_test_override));
    m->apu_pcm_test_override_valid = 0u;
#endif
    post_boot_apply(m);
    m->ime_delay = 0;
    m->serial_bits = 0;
    m->apu_sequencer_step = 0u;
    m->apu_sample_phase = 0u;
    memset(m->audio_event_ring, 0, sizeof(m->audio_event_ring));
    m->audio_event_head = 0u;
    m->audio_mix_level[0] = m->audio_mix_level[1] = 0;
    memset(m->audio_hpf_input, 0, sizeof(m->audio_hpf_input));
    memset(m->audio_hpf_output, 0, sizeof(m->audio_hpf_output));
    m->timer_signal = 0;
    m->timer_reload_pending = 0;
    m->timer_reload_remaining = 0;
    m->timer_reloaded_at = UINT64_MAX;
    m->instruction_start_half_dots = 0;
    m->serial_edge_remaining = 0;
    m->serial_active = 0;
    m->bus_unsupported = 0;
    m->bus_unsupported_address = 0u;
    m->dma_page = 0;
    m->dma_pending_page = 0;
    m->dma_index = 0;
    m->dma_phase = 0;
    m->dma_active = 0;
    m->dma_start_pending = 0;
    m->dma_cpu_blocked = 0;
    memset(&m->hdma, 0, sizeof(m->hdma));
    m->hdma.control_readback = 0xFFu;
    m->halted = 0;
    m->stopped = 0;
    m->halt_bug = 0;
    m->double_speed = 0u; /* P12-M24 */
    m->cpu_stall_kind = GBB_STALL_NONE; /* P12-M25 */
    m->cpu_stall_half_dots = 0u; /* P12-M25 */
    m->stop_switch_pending = 0u;
    m->key1_armed = 0u; /* P12-M26 */
    memset(m->frame_working, 0, sizeof(m->frame_working));
    memset(m->frame_completed, 0, sizeof(m->frame_completed));
    memset(m->rgb_working, 0, sizeof(m->rgb_working));
    memset(m->rgb_completed, 0, sizeof(m->rgb_completed));
    m->frame_generation = 0;
    m->frame_completion_half_dots = 0;
    m->ppu_dot = 0;
    m->ppu_half_phase = 0;
    m->ppu_stat_line = 0;
    m->ppu_scan_index = 0;
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
    m->time_half_dots = 0;
    m->input_event_count = 0;
    m->lockup_pc = 0;
    m->lockup_opcode = 0;
    m->locked = 0;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static uint8_t joypad_value(const gbb_instance *m) {
    uint8_t lines = 0x0Fu;
    /* MODEL: BOTH GATE-12 basis=pandocs-joyp -- P1 button and direction select lines are the same on both models */
    if ((m->joypad_select & 0x20u) == 0)
        lines &= (uint8_t)~((m->joypad_buttons >> 4) & 0x0Fu);
    if ((m->joypad_select & 0x10u) == 0)
        lines &= (uint8_t)~(m->joypad_buttons & 0x0Fu);
    return (uint8_t)(0xC0u | m->joypad_select | lines);
}

/* Request JOYP IF at the ordered software boundary that changes the selected
 * active-low pins. Pin settling, bounce, and CPU-B sampling latency are outside
 * this event-boundary model. */
/* MODEL: BOTH GATE-00 basis=model-neutral */
static void joypad_request_falling_edge(gbb_instance *m, uint8_t previous) {
    uint8_t current = (uint8_t)(joypad_value(m) & 0x0Fu);
    if ((previous & (uint8_t)~current & 0x0Fu) != 0)
        m->interrupt_flags |= 0x10u;
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static uint16_t apu_pulse_frequency(const apu_pulse_channel *pulse) {
    return (uint16_t)(pulse->frequency_low | ((pulse->control & 7u) << 8));
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static uint32_t apu_noise_period(const apu_noise_channel *noise) {
    static const uint8_t divisor[8] = {8u,16u,32u,48u,64u,80u,96u,112u};
    return ((uint32_t)divisor[noise->polynomial & 7u] << (noise->polynomial >> 4)) * 2u;
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void apu_pulse_trigger(gbb_instance *m, unsigned index) {
    apu_pulse_channel *pulse = &m->apu_pulse[index];
    int sweep_overflow = 0;
    pulse->frequency = apu_pulse_frequency(pulse);
    pulse->timer = (uint16_t)((2048u - pulse->frequency) * 64u);
    pulse->phase = 0u;
    pulse->volume = (uint8_t)(pulse->envelope >> 4);
    pulse->envelope_timer = (uint8_t)((pulse->envelope & 7u) == 0u ? 8u : pulse->envelope & 7u);
    if (pulse->length == 0u) pulse->length = 64u;
    if (index == 0u) {
        const uint8_t period = (uint8_t)((pulse->sweep >> 4) & 7u);
        const uint8_t shift = (uint8_t)(pulse->sweep & 7u);
        pulse->sweep_shadow = pulse->frequency;
        pulse->sweep_timer = period == 0u ? 8u : period;
        pulse->sweep_enabled = period != 0u || shift != 0u;
        pulse->sweep_negate_used = 0;
        if (shift != 0u) {
            int32_t delta = (int32_t)(pulse->sweep_shadow >> shift);
            if ((pulse->sweep & 8u) != 0u) {
                pulse->sweep_negate_used = 1;
                delta = -delta;
            }
            if ((int32_t)pulse->sweep_shadow + delta > 2047 ||
                (int32_t)pulse->sweep_shadow + delta < 0) sweep_overflow = 1;
        }
    }
    pulse->enabled = m->apu_power && (pulse->envelope & 0xF8u) != 0u &&
                     !sweep_overflow;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void apu_power_off(gbb_instance *m) {
    memset(m->apu_pulse, 0, sizeof(m->apu_pulse));
    memset(&m->apu_noise, 0, sizeof(m->apu_noise));
    /* Wave RAM survives NR52 power-off in this scoped DMG software model. */
    /* MODEL: UNKNOWN GATE-15 research:14 -- NR52 power-off effect on APU state and wave RAM */
    memset(&m->apu_wave, 0, offsetof(apu_wave_channel, ram));
    memset((uint8_t *)&m->apu_wave + offsetof(apu_wave_channel, position), 0,
           sizeof(m->apu_wave) - offsetof(apu_wave_channel, position));
    m->apu_nr50 = 0u;
    m->apu_nr51 = 0u;
    m->apu_sequencer_step = 0u;
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static int cpu_hram_address(uint16_t address) {
    return address >= 0xFF80u && address <= 0xFFFEu;
}

static void ppu_begin_object_scan(gbb_instance *m);

/* Cartridge-side read: ROM at 0000-7FFF and cartridge RAM or RTC at A000-BFFF, decided by the mapper and
 * not by the console. Shared by the CPU bus (read8) and the CGB OAM DMA source map (D-16), so the two
 * can never disagree about what the cartridge returns. Any other address reads $FF. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static uint8_t cart_read(const gbb_instance *m, uint16_t address) {
    /* MODEL: BOTH GATE-22 basis=cartridge-side -- ROM reads are decided by the mapper, not the console */
    if (address < 0x8000u) {
        if (m->rom == NULL || address >= m->rom_size) return 0xFFu;
        switch (m->cart.kind) {
        case CART_MBC1: {
            const size_t bank = mbc1_rom_bank(&m->cart, m->rom_size, address);
            const size_t offset = bank * 0x4000u + (size_t)(address & 0x3FFFu);
            return offset < m->rom_size ? m->rom[offset] : 0xFFu;
        }
        case CART_MBC2: {
            /* The stored bank is already translated and masked at write time. */
            const size_t bank = address < 0x4000u ? 0u : (size_t)m->cart.rom_bank_lo;
            const size_t offset = bank * 0x4000u + (size_t)(address & 0x3FFFu);
            return offset < m->rom_size ? m->rom[offset] : 0xFFu;
        }
        case CART_MBC3: {
            /* The stored bank is already translated and masked at write time. */
            const size_t bank = address < 0x4000u ? 0u : (size_t)m->cart.rom_bank_lo;
            const size_t offset = bank * 0x4000u + (size_t)(address & 0x3FFFu);
            return offset < m->rom_size ? m->rom[offset] : 0xFFu;
        }
        case CART_MBC5: {
            const size_t bank = address < 0x4000u ? 0u
                : mbc5_rom_bank(&m->cart, m->rom_size / 0x4000u);
            const size_t offset = bank * 0x4000u + (size_t)(address & 0x3FFFu);
            return offset < m->rom_size ? m->rom[offset] : 0xFFu;
        }
        case CART_ROM_ONLY:
        default:
            return m->rom[address];
        }
    }
    if (address >= 0xA000u && address <= 0xBFFFu) {
        switch (m->cart.kind) {
        case CART_MBC1:
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u)
                return m->cartridge_ram[mbc1_ram_offset(&m->cart, m->cartridge_ram_size, address)];
            return 0xFFu;
        case CART_MBC2:
            /* All 8192 addresses echo the 512 cells; upper nibble reads as 1s. */
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size == MBC2_RAM_BYTES)
                return m->cartridge_ram[address & 0x1FFu];
            return 0xFFu;
        case CART_MBC3:
            /* Selections $00-$03 reach RAM, $08-$0C the latched RTC bytes on timer
             * types; every other value maps nothing. */
            if (m->cart.ram_enabled && m->cart.has_timer &&
                m->cart.ram_bank >= 0x08u && m->cart.ram_bank <= 0x0Cu)
                return rtc_read_mask(m->cart.ram_bank - 0x08u,
                                     m->cart.rtc_l[m->cart.ram_bank - 0x08u]);
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u && m->cart.ram_bank <= 0x03u) {
                const size_t banks = m->cartridge_ram_size / 0x2000u;
                const size_t bank = (size_t)m->cart.ram_bank & (banks - 1u);
                return m->cartridge_ram[bank * 0x2000u + (size_t)(address & 0x1FFFu)];
            }
            return 0xFFu;
        case CART_MBC5:
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u) {
                const size_t banks = m->cartridge_ram_size / 0x2000u;
                const size_t bank = (size_t)m->cart.ram_bank & (banks - 1u);
                return m->cartridge_ram[bank * 0x2000u + (size_t)(address & 0x1FFFu)];
            }
            return 0xFFu;
        case CART_ROM_ONLY:
        default:
            return 0xFFu;
        }
    }
    return 0xFFu;
}

/* MODEL: CGB_ONLY GATE-92 GUARD=model_is_cgb -- a visible HBlank edge latches one request for an armed block */
static void hdma_request(gbb_instance *m) {
    /* A manual HALT pauses ordinary admission. An already admitted block is
     * owned by the scheduler and continues through its active state. */
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB ||
        (m->halted && !GBB_P13_MUT(48))) return; /* P13-05-M09: HALT admission */
    if (m->hdma.mode == 1u && !m->hdma.active && !m->hdma.pending_hblank &&
        m->hdma.blocks_remaining != 0u)
        m->hdma.pending_hblank = 1u;
}

/* MODEL: CGB_ONLY GATE-93 GUARD=model_is_cgb -- HDMA preflight accepts only cartridge ROM/RAM and direct WRAM windows */
static int hdma_source_valid(const gbb_instance *m, uint16_t address) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB) return 0;
    if (address < 0x8000u)
        return m->rom != NULL;
    return (address >= 0xA000u && address <= 0xBFFFu) ||
           (address >= 0xC000u && address <= 0xDFFFu);
}

/* MODEL: CGB_ONLY GATE-94 GUARD=model_is_cgb -- HDMA reads only the reviewed mapper or WRAM storage path */
static int hdma_source_read(const gbb_instance *m, uint16_t address, uint8_t *value) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB || value == NULL ||
        !hdma_source_valid(m, address)) return 0;
    if (address < 0x8000u || (address >= 0xA000u && address <= 0xBFFFu))
        *value = cart_read(m, address);
    else
        *value = *wram_byte(m, address);
    return 1;
}

/* MODEL: CGB_ONLY GATE-95 GUARD=model_is_cgb -- validate an entire block before admission and sample VBK once */
static int hdma_admit_block(gbb_instance *m) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB) return 0;
    if (!m->hdma.pending_hblank) return 1;
    if (m->hdma.blocks_remaining == 0u ||
        m->hdma.source_cursor > UINT16_MAX - 15u ||
        m->hdma.destination_cursor < 0x8000u ||
        m->hdma.destination_cursor > 0x9FF0u) return 0;
    for (unsigned i = 0u; i < 16u; ++i) {
        const uint16_t address = (uint16_t)(m->hdma.source_cursor + i);
        if (!hdma_source_valid(m, address)) return 0;
    }
    m->hdma.pending_hblank = 0u;
    m->hdma.active = 1u;
    m->hdma.byte_index = 0u;
    m->hdma.byte_phase = 0u;
    m->hdma.block_vram_bank = m->vram_bank;
    return 1;
}

/* MODEL: CGB_ONLY GATE-98 GUARD=model_is_cgb -- invalid block stop retains FF55 remaining status */
static void hdma_stop_at_invalid_block(gbb_instance *m, uint16_t address) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB) return;
    m->bus_unsupported = 1u;
    m->bus_unsupported_address = address;
    m->hdma.active = 0u;
    m->hdma.pending_hblank = 0u;
    m->hdma.mode = 0u;
    m->hdma.byte_index = 0u;
    m->hdma.byte_phase = 0u;
    if (m->hdma.blocks_remaining != 0u)
        m->hdma.control_readback = (uint8_t)(0x80u | ((m->hdma.blocks_remaining - 1u) & 0x7Fu));
}

/* MODEL: CGB_ONLY GATE-96 GUARD=model_is_cgb -- HDMA commits one byte every four master half-dots after OAM and before PPU */
static void hdma_advance_half_dot(gbb_instance *m) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB || !m->hdma.active) return;
    const int byte_limit = GBB_P13_MUT(47) && m->double_speed != 0u
        ? 2 : 4 + GBB_P13_DURATION_OFFSET;
    if ((int)++m->hdma.byte_phase < byte_limit) return; /* P13-05-M08 */
    m->hdma.byte_phase = 0u;
    const uint16_t source = (uint16_t)(m->hdma.source_cursor + m->hdma.byte_index);
    const unsigned destination = (unsigned)(m->hdma.destination_cursor - 0x8000u) +
                                 m->hdma.byte_index;
    uint8_t value = 0xFFu;
    if (destination >= GBB_VRAM_BANK_SIZE ||
        !hdma_source_read(m, source, &value)) {
        hdma_stop_at_invalid_block(m, source);
        return;
    }
    const unsigned write_bank = m->hdma.block_vram_bank ^ (GBB_P13_MUT(43) ? 1u : 0u); /* P13-05-M04 */
    if (!GBB_P13_MUT(41))
        m->vram[write_bank][destination] = value; /* P13-05-M02 */
    if (GBB_P13_MUT(42) && m->hdma.byte_index == 15u &&
        destination + 1u < GBB_VRAM_BANK_SIZE)
        m->vram[write_bank][destination + 1u] = value; /* P13-05-M03 */
    if (++m->hdma.byte_index != 16u) return;

    m->hdma.active = 0u;
    m->hdma.byte_index = 0u;
    if (m->hdma.blocks_remaining != 0u) --m->hdma.blocks_remaining;
    if (GBB_P13_MUT(45) && m->hdma.blocks_remaining != 0u)
        --m->hdma.blocks_remaining; /* P13-05-M06 */
    m->hdma.source_cursor = (uint16_t)(m->hdma.source_cursor + 16u);
    m->hdma.destination_cursor += 16u;
    if (m->hdma.blocks_remaining == 0u) {
        m->hdma.mode = 0u;
        m->hdma.pending_hblank = 0u;
        m->hdma.control_readback = 0xFFu;
    } else {
        m->hdma.control_readback = (uint8_t)((m->hdma.blocks_remaining - 1u) & 0x7Fu);
        if (m->hdma.mode == 2u) m->hdma.pending_hblank = 1u;
    }
    if (GBB_P13_MUT(51)) speed_switch_apply_realign(m); /* P13-05-M12 */
}

/* MODEL: CGB_ONLY GATE-97 GUARD=model_is_cgb -- FF51-55 maintain bounded cursor and transfer state */
static void hdma_register_write(gbb_instance *m, uint16_t address, uint8_t value) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB) return;
    switch (address) {
    case 0xFF51u:
        if (m->hdma.mode != 0u || m->hdma.active || m->hdma.pending_hblank) return;
        m->hdma.source_high = value;
        m->hdma.source_cursor = (uint16_t)(((uint16_t)value << 8) |
                                           (m->hdma.source_cursor & 0x00FFu));
        break;
    case 0xFF52u:
        if (m->hdma.mode != 0u || m->hdma.active || m->hdma.pending_hblank) return;
        m->hdma.source_low = (uint8_t)(value & 0xF0u);
        m->hdma.source_cursor = (uint16_t)((m->hdma.source_cursor & 0xFF00u) |
                                           m->hdma.source_low);
        break;
    case 0xFF53u:
        if (m->hdma.mode != 0u || m->hdma.active || m->hdma.pending_hblank) return;
        m->hdma.destination_high = (uint8_t)(value & 0x1Fu);
        m->hdma.destination_cursor = 0x8000u |
            ((uint16_t)m->hdma.destination_high << 8) |
            (m->hdma.destination_cursor & 0x00FFu);
        break;
    case 0xFF54u:
        if (m->hdma.mode != 0u || m->hdma.active || m->hdma.pending_hblank) return;
        m->hdma.destination_low = (uint8_t)(GBB_P13_MUT(44) ? value : (value & 0xF0u)); /* P13-05-M05 */
        m->hdma.destination_cursor = (m->hdma.destination_cursor & 0xFF00u) |
                                     m->hdma.destination_low;
        break;
    case 0xFF55u:
        if (m->hdma.mode == 2u || m->hdma.active) return;
        if (m->hdma.mode == 1u) {
            if ((value & 0x80u) == 0u) {
                const uint16_t retained_blocks = m->hdma.blocks_remaining;
                m->hdma.mode = 0u;
                m->hdma.pending_hblank = 0u;
                m->hdma.blocks_remaining = 0u;
                m->hdma.byte_index = 0u;
                m->hdma.byte_phase = 0u;
                m->hdma.control_readback = GBB_P13_MUT(46)
                    ? (uint8_t)(0x80u | ((retained_blocks - 1u) & 0x7Fu))
                    : (uint8_t)(0x80u | (value & 0x7Fu)); /* P13-05-M07 */
            } else {
                m->hdma.blocks_remaining = (uint16_t)((value & 0x7Fu) + 1u);
                m->hdma.control_readback = (uint8_t)(value & 0x7Fu);
            }
            break;
        }
        m->hdma.mode = (value & 0x80u) != 0u ? 1u : 2u;
        m->hdma.active = 0u;
        m->hdma.pending_hblank = m->hdma.mode == 2u ? 1u : 0u;
        m->hdma.blocks_remaining = (uint16_t)((value & 0x7Fu) + 1u);
        m->hdma.byte_index = 0u;
        m->hdma.byte_phase = 0u;
        m->hdma.control_readback = (uint8_t)(value & 0x7Fu);
        if (m->hdma.mode == 1u &&
            ((m->lcdc & 0x80u) == 0u ||
             (m->ly < GBB_FRAME_HEIGHT && m->ppu_mode == 0u)))
            m->hdma.pending_hblank = 1u;
        break;
    default: break;
    }
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static uint8_t read8(const gbb_instance *m, uint16_t address) {
    /* MODEL: UNKNOWN GATE-16 expected-failure:cgb-separate-buses -- OAM-DMA CPU bus conflict: CGB uses separate buses (D-17) */
    if (m->dma_active && m->dma_cpu_blocked &&
        !cpu_hram_address(address) && address != 0xFF46u) return 0xFFu;
    if (address == 0xFF00) return joypad_value(m);
    if (address == 0xFF04) return m->div;
    if (address == 0xFF05) return m->tima;
    if (address == 0xFF06) return m->tma;
    if (address == 0xFF07) return (uint8_t)(0xF8u | m->tac);
    if (address == 0xFF01) return m->serial_data;
    /* MODEL: UNKNOWN GATE-17 research:14 -- SC unused bits read differently on CGB (fast clock bit) */
    if (address == 0xFF02) return (uint8_t)(0x7Eu | m->serial_control);
    /* MODEL: UNKNOWN GATE-18 research:14 -- APU read masks, including NR52 length bits */
    if (address == 0xFF10) return (uint8_t)(0x80u | m->apu_pulse[0].sweep);
    if (address == 0xFF11) return (uint8_t)(0x3Fu | (m->apu_pulse[0].duty_length & 0xC0u));
    if (address == 0xFF12) return m->apu_pulse[0].envelope;
    if (address == 0xFF13) return 0xFFu;
    if (address == 0xFF14) return (uint8_t)(0xBFu | (m->apu_pulse[0].control & 0x40u));
    if (address == 0xFF16) return (uint8_t)(0x3Fu | (m->apu_pulse[1].duty_length & 0xC0u));
    if (address == 0xFF17) return m->apu_pulse[1].envelope;
    if (address == 0xFF18) return 0xFFu;
    if (address == 0xFF19) return (uint8_t)(0xBFu | (m->apu_pulse[1].control & 0x40u));
    if (address == 0xFF1A) return (uint8_t)(0x7Fu | (m->apu_wave.dac & 0x80u));
    if (address == 0xFF1B) return 0xFFu;
    if (address == 0xFF1C) return (uint8_t)(0x9Fu | (m->apu_wave.level & 0x60u));
    if (address == 0xFF1D) return 0xFFu;
    if (address == 0xFF1E) return (uint8_t)(0xBFu | (m->apu_wave.control & 0x40u));
    if (address == 0xFF20) return 0xFFu;
    if (address == 0xFF21) return m->apu_noise.envelope;
    if (address == 0xFF22) return m->apu_noise.polynomial;
    if (address == 0xFF23) return (uint8_t)(0xBFu | (m->apu_noise.control & 0x40u));
    /* MODEL: UNKNOWN GATE-19 research:14 -- wave RAM access aliasing while the channel is enabled */
    if (address >= 0xFF30u && address <= 0xFF3Fu) {
        unsigned index = address - 0xFF30u;
        /* Active access aliases the current byte in this revision-scoped software model. */
        if (m->apu_wave.enabled) index = m->apu_wave.position >> 1;
        return m->apu_wave.ram[index];
    }
    if (address == 0xFF24) return m->apu_nr50;
    if (address == 0xFF25) return m->apu_nr51;
    if (address == 0xFF26)
        return (uint8_t)(0x70u | (m->apu_power ? 0x80u : 0u) |
                         (m->apu_pulse[0].enabled ? 1u : 0u) |
                         (m->apu_pulse[1].enabled ? 2u : 0u) |
                         (m->apu_wave.enabled ? 4u : 0u) |
                         (m->apu_noise.enabled ? 8u : 0u));
    if (address == 0xFF40) return m->lcdc;
    /* MODEL: UNKNOWN GATE-20 research:14 -- STAT mode and coincidence bits at LCD transitions; CGB transition timing is unresearched and deferred by D-09/D-12 */
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
    /* MODEL: CGB_ONLY GATE-72 GUARD=model_is_cgb -- FF4C-FF7F decode through io_visibility[]; the DMG profile falls through unchanged (D-09) */
    if (address >= 0xFF4Cu && address <= 0xFF7Fu && model_is_cgb(m)) return io_read_cgb(m, address);
    if (address == 0xFF0F) return (uint8_t)(0xE0u | m->interrupt_flags);
    /* MODEL: CGB_ONLY GATE-21 GUARD=model_is_cgb -- IE bits 5-7 are stored on the CGB profile (unused_hwio-C/-GS); DMG reads them as 1 (OQ2) */
    if (address == 0xFFFF) return model_is_cgb(m) ? m->ie : (uint8_t)(0xE0u | m->ie);
    if (address >= 0x8000 && address <= 0x9FFF)
        return cpu_vram_access_allowed(m) ? m->vram[m->vram_bank][address - 0x8000] : 0xFF;
    if (address >= 0xFE00 && address <= 0xFE9F)
        return cpu_oam_access_allowed(m) ? m->oam[address - 0xFE00] : 0xFF;
    if (address < 0x8000u || (address >= 0xA000u && address <= 0xBFFFu)) return cart_read(m, address);
    /* MODEL: BOTH GATE-23 basis=wram-echo-map -- work RAM and echo mapping; CGB WRAM banking is selected in wram_byte */
    if (address >= 0xC000 && address <= 0xFDFF) return *wram_byte(m, address);
    if (address >= 0xFF80 && address <= 0xFFFE) return m->hram[address - 0xFF80];
    return 0xFF;
}

static void advance_devices_to(gbb_instance *m, uint64_t target);

/* MODEL: BOTH GATE-00 basis=model-neutral */
static uint8_t bus_read(gbb_instance *m, uint16_t address, uint64_t offset) {
    advance_devices_to(m, m->instruction_start_half_dots + (offset >> m->double_speed)); /* P12-M18 */ /* bus-read */
    uint8_t value = read8(m, address);
    observe_bus(m, 0, address, 1, value);
    return value;
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static unsigned timer_bit(uint8_t tac) {
    static const uint8_t bits[4] = {9, 3, 5, 7};
    return bits[tac & 3u];
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static int timer_input(const gbb_instance *m) {
    return (m->tac & 4u) != 0 && ((m->divider_counter >> timer_bit(m->tac)) & 1u) != 0;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void timer_increment(gbb_instance *m, uint64_t at) {
    if (m->timer_reload_pending) return;
    /* MODEL: UNKNOWN GATE-24 research:14 -- TIMA overflow and reload timing */
    if (m->tima == 0xFFu) {
        m->tima = 0;
        m->timer_reload_pending = 1;
        m->timer_reload_remaining = 4u; /* P12-M15 */
        observe_bus(m, 0, 0xFF05, 3, m->tima);
        diagnostic_add(m, GBB_DIAGNOSTIC_TIMER, at, 0xFF05, m->tima);
    } else {
        ++m->tima;
        diagnostic_add(m, GBB_DIAGNOSTIC_TIMER, at, 0xFF05, m->tima);
    }
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void timer_set_signal(gbb_instance *m, int next, uint64_t at) {
    if (m->timer_signal && !next) timer_increment(m, at);
    m->timer_signal = next;
}

/* MODEL: BOTH GATE-00 basis=cpu-tick-countdown-converts-to-master-half-dots */
static uint32_t timer_reload_hd(const gbb_instance *m) {
    return (uint32_t)m->timer_reload_remaining << (1u - (m->double_speed & 1u));
}

static void apu_sequencer_clock(gbb_instance *m);

/* MODEL: BOTH GATE-00 basis="DIV reset edge semantics are shared by both CPU models" */
static void divider_reset(gbb_instance *m, int clock_apu_edge) {
    const uint16_t reset_tap = m->double_speed ? 0x2000u : 0x1000u; /* P12-M4 */
    const int apu_falling_edge = (m->divider_counter & reset_tap) != 0u;
    m->divider_counter = 0u;
    m->div = 0u;
    m->divider_phase = 0u;
    timer_set_signal(m, timer_input(m), m->time_half_dots);
    if (clock_apu_edge && apu_falling_edge) apu_sequencer_clock(m);
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void write8(gbb_instance *m, uint16_t address, uint8_t value) {
    /* MODEL: UNKNOWN GATE-25 expected-failure:cgb-separate-buses -- OAM-DMA CPU bus conflict: CGB uses separate buses (D-17) */
    if (m->dma_active && m->dma_cpu_blocked &&
        !cpu_hram_address(address) && address != 0xFF46u) return;
    /* MODEL: BOTH GATE-26 basis=cartridge-side -- mapper register writes are decided by the cartridge */
    if (address < 0x8000u) {
        switch (m->cart.kind) {
        case CART_MBC1:
            if (address < 0x2000u)
                m->cart.ram_enabled = (value & 0x0Fu) == 0x0Au;
            else if (address < 0x4000u)
                m->cart.rom_bank_lo = value & 0x1Fu;
            else if (address < 0x6000u)
                m->cart.rom_bank_hi = value & 0x03u;
            else
                m->cart.mbc1_mode = value & 0x01u;
            break;
        case CART_MBC2:
            /* Address bit 8 chooses the register; $4000-$7FFF is unmapped. */
            if (address < 0x4000u) {
                if ((address & 0x0100u) == 0u) {
                    m->cart.ram_enabled = (value & 0x0Fu) == 0x0Au;
                } else {
                    /* Translate zero before masking, as MBC1 does. */
                    size_t bank = value & 0x0Fu;
                    if (bank == 0u) bank = 1u;
                    m->cart.rom_bank_lo = (uint8_t)(bank & (m->rom_size / 0x4000u - 1u));
                }
            }
            break;
        case CART_MBC3:
            if (address < 0x2000u) {
                m->cart.ram_enabled = (value & 0x0Fu) == 0x0Au;
            } else if (address < 0x4000u) {
                /* Seven bits, zero becomes one, then wrap to the image. */
                size_t bank = value & 0x7Fu;
                if (bank == 0u) bank = 1u;
                m->cart.rom_bank_lo = (uint8_t)(bank & (m->rom_size / 0x4000u - 1u));
            } else if (address < 0x6000u) {
                /* This is a software-model decision, not hardware-qualified: values
                 * $04-$07 and $0D-$FF map nothing (SameBoy aliases with & 3, mGBA
                 * decodes the low nibble). Stored whole so the RTC plan can map
                 * $08-$0C. */
                m->cart.ram_bank = value;
            } else if (address < 0x8000u && m->cart.has_timer) {
                /* Latching on exactly $00 then $01 is a project decision (the
                 * common emulator behaviour), not a hardware-confirmed rule. */
                rtc_latch_write(&m->cart, m->time_half_dots, value);
            }
            break;
        case CART_MBC5:
            if (address < 0x2000u)
                m->cart.ram_enabled = (value & 0x0Fu) == 0x0Au;
            else if (address < 0x3000u)
                m->cart.rom_bank_lo = value;
            else if (address < 0x4000u)
                m->cart.rom_bank_hi = value & 0x01u;
            else if (address < 0x6000u) {
                /* Rumble carts give bit 3 to the motor line, leaving 3 RAM bank
                 * bits; the line is host-observable but never reaches the RAM index. */
                if (m->cart.has_rumble) {
                    const uint8_t line = (uint8_t)((value >> 3) & 1u);
                    m->cart.ram_bank = value & 0x07u;
                    if (line != m->cart.rumble_on) {
                        m->cart.rumble_on = line;
                        if (m->cart.rumble_changes != UINT64_MAX) ++m->cart.rumble_changes;
                    }
                } else {
                    m->cart.ram_bank = value & 0x0Fu;
                }
            }
            break;
        case CART_ROM_ONLY:
        default:
            break;
        }
    }
    else if (address >= 0x8000 && address <= 0x9FFF) {
        if (cpu_vram_access_allowed(m)) m->vram[m->vram_bank][address - 0x8000] = value;
    }
    else if (address >= 0xFE00 && address <= 0xFE9F) {
        if (cpu_oam_access_allowed(m)) m->oam[address - 0xFE00] = value;
    }
    else if (address >= 0xA000u && address <= 0xBFFFu) {
        switch (m->cart.kind) {
        case CART_MBC1:
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u) {
                const size_t offset =
                    mbc1_ram_offset(&m->cart, m->cartridge_ram_size, address);
                const uint8_t previous = m->cartridge_ram[offset];
                if (previous != value) {
                    m->cartridge_ram[offset] = value;
                    if (m->cart.has_battery &&
                        m->battery_generation != UINT64_MAX)
                        ++m->battery_generation;
                }
            }
            break;
        case CART_MBC2:
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size == MBC2_RAM_BYTES) {
                const size_t offset = address & 0x1FFu;
                const uint8_t canonical = (uint8_t)(0xF0u | (value & 0x0Fu));
                if (m->cartridge_ram[offset] != canonical) {
                    m->cartridge_ram[offset] = canonical;
                    if (m->cart.has_battery &&
                        m->battery_generation != UINT64_MAX)
                        ++m->battery_generation;
                }
            }
            break;
        case CART_MBC3:
            if (m->cart.ram_enabled && m->cart.has_timer &&
                m->cart.ram_bank >= 0x08u && m->cart.ram_bank <= 0x0Cu) {
                /* bus_write advanced the devices first, so time_half_dots is the
                 * write timestamp. */
                if (rtc_write_register(&m->cart, m->time_half_dots,
                                       (unsigned)m->cart.ram_bank - 0x08u, value) &&
                    m->cart.has_battery && m->battery_generation != UINT64_MAX)
                    ++m->battery_generation;
            } else if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u && m->cart.ram_bank <= 0x03u) {
                const size_t banks = m->cartridge_ram_size / 0x2000u;
                const size_t offset = ((size_t)m->cart.ram_bank & (banks - 1u)) * 0x2000u +
                                      (size_t)(address & 0x1FFFu);
                if (m->cartridge_ram[offset] != value) {
                    m->cartridge_ram[offset] = value;
                    if (m->cart.has_battery &&
                        m->battery_generation != UINT64_MAX)
                        ++m->battery_generation;
                }
            }
            break;
        case CART_MBC5:
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u) {
                const size_t banks = m->cartridge_ram_size / 0x2000u;
                const size_t offset = ((size_t)m->cart.ram_bank & (banks - 1u)) * 0x2000u +
                                      (size_t)(address & 0x1FFFu);
                if (m->cartridge_ram[offset] != value) {
                    m->cartridge_ram[offset] = value;
                    if (m->cart.has_battery &&
                        m->battery_generation != UINT64_MAX)
                        ++m->battery_generation;
                }
            }
            break;
        case CART_ROM_ONLY:
        default:
            break;
        }
    }
    /* MODEL: UNKNOWN GATE-27 research:14 -- JOYP write select and IF side effects */
    else if (address == 0xFF00) {
        uint8_t previous = (uint8_t)(joypad_value(m) & 0x0Fu);
        m->joypad_select = (uint8_t)(value & 0x30u);
        joypad_request_falling_edge(m, previous);
    }
    /* MODEL: UNKNOWN GATE-28 research:14 -- LCD on and off timing */
    else if (address == 0xFF40) {
        uint8_t old = m->lcdc;
        m->lcdc = value;
        if ((value & 0x80u) == 0) {
            if (m->hdma.mode == 1u && !m->hdma.active)
                m->hdma.pending_hblank = 0u;
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
            /* MODEL: CGB_ONLY GATE-78 GUARD=model_is_cgb -- LCD off blanks the RGB working frame to white; the completed RGB frame is kept (D-02) */
            if (model_is_cgb(m)) {
                for (unsigned i = 0; i < GBB_FRAME_PIXELS; ++i) m->rgb_working[i] = 0x7FFFu;
            }
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
    /* MODEL: UNKNOWN GATE-29 research:14 -- STAT write spurious interrupt quirk is DMG-specific */
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
    /* MODEL: BOTH GATE-30 basis="OAM DMA start requests and byte period are shared; its CPU-rate conversion is declared by GATE-90" -- FF46 start request */
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
    /* MODEL: BOTH GATE-31 basis="DIV reset and frame-sequencer edge use the same selected-speed tap on both models, D-11" -- DIV write */
    else if (address == 0xFF04) {
        divider_reset(m, 1);
    }
    else if (address == 0xFF05) {
        if (m->time_half_dots == m->timer_reloaded_at) { /* reload wins this sampled write */ }
        else { m->tima = value; m->timer_reload_pending = 0; }
    }
    else if (address == 0xFF06) {
        m->tma = value;
        if (m->time_half_dots == m->timer_reloaded_at) m->tima = value;
    }
    /* MODEL: UNKNOWN GATE-32 research:14 -- TAC write glitch timing */
    else if (address == 0xFF07) {
        m->tac = (uint8_t)(value & 7u);
        timer_set_signal(m, timer_input(m), m->time_half_dots);
    }
    /* MODEL: UNKNOWN GATE-33 research:14 -- serial data and control write behaviour */
    else if (address == 0xFF01) {
        if (m->serial_active) { m->bus_unsupported = 1; m->bus_unsupported_address = address; }
        else m->serial_data = value;
    }
    else if (address == 0xFF02) {
        if (m->serial_active) {
            m->bus_unsupported = 1;
            m->bus_unsupported_address = address;
        } else {
            m->serial_control = (uint8_t)(value & 0x81u);
            if (value & 0x80u) {
                m->serial_active = 1;
                m->serial_bits = 0;
                if (value & 1u) m->serial_edge_remaining = 512u;
            }
        }
    }
    /* MODEL: UNKNOWN GATE-34 research:14 -- NR52 power-off and power-on behaviour */
    else if (address == 0xFF26) {
        if ((value & 0x80u) == 0u) { m->apu_power = 0u; apu_power_off(m); }
        else if (!m->apu_power) { m->apu_power = 1u; m->apu_sequencer_step = 0u; }
    }
    /* MODEL: UNKNOWN GATE-35 research:14 -- wave RAM write aliasing while the channel is enabled */
    else if (address >= 0xFF30u && address <= 0xFF3Fu) {
        unsigned index = address - 0xFF30u;
        /* CPU-B revision variation in active wave-RAM access is not hardware-qualified. */
        if (m->apu_wave.enabled) index = m->apu_wave.position >> 1;
        m->apu_wave.ram[index] = value;
    }
    /* MODEL: UNKNOWN GATE-36 research:14 -- APU register writes while powered on */
    else if (m->apu_power && address == 0xFF10) {
        if (m->apu_pulse[0].sweep_negate_used &&
            (m->apu_pulse[0].sweep & 8u) != 0u && (value & 8u) == 0u)
            m->apu_pulse[0].enabled = 0;
        m->apu_pulse[0].sweep = (uint8_t)(value & 0x7Fu);
    }
    else if (m->apu_power && address == 0xFF11) {
        m->apu_pulse[0].duty_length = value;
        m->apu_pulse[0].length = (uint16_t)(64u - (value & 0x3Fu));
    }
    else if (m->apu_power && address == 0xFF12) {
        m->apu_pulse[0].envelope = value;
        if ((value & 0xF8u) == 0u) m->apu_pulse[0].enabled = 0;
    }
    else if (m->apu_power && address == 0xFF13) m->apu_pulse[0].frequency_low = value;
    else if (m->apu_power && address == 0xFF14) {
        m->apu_pulse[0].control = (uint8_t)(value & 0x47u);
        if ((value & 0x80u) != 0u) apu_pulse_trigger(m, 0u);
    }
    else if (m->apu_power && address == 0xFF16) {
        m->apu_pulse[1].duty_length = value;
        m->apu_pulse[1].length = (uint16_t)(64u - (value & 0x3Fu));
    }
    else if (m->apu_power && address == 0xFF17) {
        m->apu_pulse[1].envelope = value;
        if ((value & 0xF8u) == 0u) m->apu_pulse[1].enabled = 0;
    }
    else if (m->apu_power && address == 0xFF18) m->apu_pulse[1].frequency_low = value;
    else if (m->apu_power && address == 0xFF19) {
        m->apu_pulse[1].control = (uint8_t)(value & 0x47u);
        if ((value & 0x80u) != 0u) apu_pulse_trigger(m, 1u);
    }
    else if (m->apu_power && address == 0xFF1A) {
        m->apu_wave.dac = (uint8_t)(value & 0x80u);
        if (m->apu_wave.dac == 0u) m->apu_wave.enabled = 0;
    }
    else if (m->apu_power && address == 0xFF1B) {
        m->apu_wave.length_reg = value;
        m->apu_wave.length = (uint16_t)(256u - value);
    }
    else if (m->apu_power && address == 0xFF1C) m->apu_wave.level = (uint8_t)(value & 0x60u);
    else if (m->apu_power && address == 0xFF1D) m->apu_wave.frequency_low = value;
    else if (m->apu_power && address == 0xFF1E) {
        m->apu_wave.control = (uint8_t)(value & 0x47u);
        if ((value & 0x80u) != 0u) {
            uint16_t frequency = (uint16_t)(m->apu_wave.frequency_low |
                                            ((m->apu_wave.control & 7u) << 8));
            m->apu_wave.timer = (uint16_t)((2048u - frequency) * 2u);
            m->apu_wave.position = 0u;
            if (m->apu_wave.length == 0u) m->apu_wave.length = 256u;
            m->apu_wave.enabled = m->apu_power && m->apu_wave.dac != 0u;
        }
    }
    else if (m->apu_power && address == 0xFF20) {
        m->apu_noise.length_reg = (uint8_t)(value & 0x3Fu);
        m->apu_noise.length = (uint16_t)(64u - m->apu_noise.length_reg);
    }
    else if (m->apu_power && address == 0xFF21) {
        m->apu_noise.envelope = value;
        if ((value & 0xF8u) == 0u) m->apu_noise.enabled = 0;
    }
    else if (m->apu_power && address == 0xFF22) m->apu_noise.polynomial = value;
    else if (m->apu_power && address == 0xFF23) {
        m->apu_noise.control = (uint8_t)(value & 0x40u);
        if ((value & 0x80u) != 0u) {
            m->apu_noise.timer = apu_noise_period(&m->apu_noise);
            m->apu_noise.lfsr = 0x7FFFu;
            m->apu_noise.volume = (uint8_t)(m->apu_noise.envelope >> 4);
            m->apu_noise.envelope_timer = (uint8_t)((m->apu_noise.envelope & 7u) == 0u
                ? 8u : m->apu_noise.envelope & 7u);
            if (m->apu_noise.length == 0u) m->apu_noise.length = 64u;
            m->apu_noise.enabled = m->apu_power && (m->apu_noise.envelope & 0xF8u) != 0u;
        }
    }
    else if (m->apu_power && address == 0xFF24) m->apu_nr50 = value;
    else if (m->apu_power && address == 0xFF25) m->apu_nr51 = value;
    /* MODEL: CGB_ONLY GATE-73 GUARD=model_is_cgb -- FF4C-FF7F decode through io_visibility[]; a no-op on the DMG profile (C4) */
    else if (address >= 0xFF4Cu && address <= 0xFF7Fu) { if (model_is_cgb(m)) io_write_cgb(m, address, value); }
    else if (address == 0xFF0F) m->interrupt_flags = (uint8_t)(value & 0x1Fu);
    /* MODEL: CGB_ONLY GATE-37 GUARD=model_is_cgb -- IE bits 5-7 are stored on the CGB profile; DMG keeps IE & $1F (OQ2) */
    else if (address == 0xFFFF) m->ie = (uint8_t)(value & (model_is_cgb(m) ? 0xFFu : 0x1Fu));
    /* MODEL: BOTH GATE-38 basis=wram-echo-map -- work RAM and echo mapping; CGB WRAM banking is selected in wram_byte */
    else if (address >= 0xC000 && address <= 0xFDFF) *wram_byte_mut(m, address) = value;
    else if (address >= 0xFF80 && address <= 0xFFFE) m->hram[address - 0xFF80] = value;
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void bus_write(gbb_instance *m, uint16_t address, uint8_t value, uint64_t offset) {
    uint64_t timestamp = m->instruction_start_half_dots + (offset >> m->double_speed); /* P12-M18 */ /* bus-write */
    /* TMA feeds the reload when the write shares its exact reload timestamp. */
    if (address == 0xFF06 && m->timer_reload_pending && timestamp >= m->time_half_dots &&
        timestamp - m->time_half_dots == timer_reload_hd(m))
        m->tma = value;
    advance_devices_to(m, timestamp);
    observe_bus(m, 0, address, 2, value);
    write8(m, address, value);
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int read_supported_map(const gbb_instance *m, uint16_t address) {
    /* MODEL: CGB_ONLY GATE-39 GUARD=model_is_cgb -- on the CGB profile FF00-FF7F readability comes from io_visibility[]; the DMG chain below is unchanged */
    if (m != NULL && model_is_cgb(m) && address >= 0xFF00u && address <= 0xFF7Fu)
        return io_cgb_cell(m, address)->kind != IO_DEFERRED_RW;
    /* MODEL: UNKNOWN GATE-40 research:14 -- FEA0-FEFF stays fail-closed on both profiles this phase (A6) */
    return address < 0xA000 || (address >= 0xFE00 && address <= 0xFE9F) ||
           (address >= 0xA000 && address <= 0xBFFF && m != NULL &&
            ((m->cartridge_ram != NULL && m->cartridge_ram_size != 0u) ||
             m->cart.ram_window_mapped)) ||
           address == 0xFF00 || address == 0xFF01 || address == 0xFF02 ||
           (address >= 0xFF10 && address <= 0xFF14) ||
           (address >= 0xFF16 && address <= 0xFF19) ||
           (address >= 0xFF1A && address <= 0xFF1E) ||
           (address >= 0xFF20 && address <= 0xFF23) ||
           (address >= 0xFF30 && address <= 0xFF3F) ||
           (address >= 0xFF24 && address <= 0xFF26) ||
           (address >= 0xFF04 && address <= 0xFF07) || address == 0xFF0F || address == 0xFFFF ||
           (address >= 0xFF40 && address <= 0xFF46) ||
           (address >= 0xFF47 && address <= 0xFF4B) ||
           (address >= 0xC000 && address <= 0xDFFF) ||
           (address >= 0xE000 && address <= 0xFDFF) ||
           (address >= 0xFF80 && address <= 0xFFFE);
}

/* The pre-flight check also records the refused address for the test seam; it changes nothing the
 * guest can observe. */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int read_supported(gbb_instance *m, uint16_t address) {
    const int ok = read_supported_map(m, address);
    if (!ok && m != NULL) m->bus_unsupported_address = address;
    return ok;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint16_t hl(const gbb_instance *m) { return (uint16_t)(((uint16_t)m->h << 8) | m->l); }
static unsigned pending_interrupt(const gbb_instance *m);

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void shift_external_serial(gbb_instance *m, uint8_t bit) {
    if (!m->serial_active || (m->serial_control & 1u) != 0) return;
    m->serial_data = (uint8_t)((m->serial_data << 1) | bit);
    if (++m->serial_bits == 8u) {
        m->serial_active = 0;
        m->serial_control &= 1u;
        m->interrupt_flags |= 0x08u;
    }
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void apply_input_events_now(gbb_instance *m) {
    while (m->input_event_count != 0 &&
           m->input_events[0].at_half_dots == m->time_half_dots) {
        gbb_input_event event = m->input_events[0];
        --m->input_event_count;
        if (m->input_event_count != 0)
            memmove(m->input_events, m->input_events + 1,
                    m->input_event_count * sizeof(m->input_events[0]));
        /* MODEL: UNKNOWN GATE-41 research:14 -- STOP wake conditions */
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

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint16_t instruction_address(const gbb_instance *m, uint16_t pc, unsigned offset) {
    /* MODEL: BOTH GATE-42 basis="no SM83 opcode difference" -- HALT bug PC repeat is an SM83 trait */
    if (m->halt_bug && offset != 0) --offset;
    return (uint16_t)(pc + offset);
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint8_t instruction_byte(const gbb_instance *m, uint16_t pc, unsigned offset) {
    return read8(m, instruction_address(m, pc, offset));
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
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
    uint8_t low = m->vram[0][address];
    uint8_t high = m->vram[0][address + 1u];
    return (uint8_t)(((low >> bit) & 1u) | (((high >> bit) & 1u) << 1));
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static int ppu_window_visible_at(const gbb_instance *m, unsigned x) {
    if ((m->lcdc & 0x21u) != 0x21u || m->ly < m->wy || m->wx > 166u)
        return 0;
    int left = (int)m->wx - 7;
    return (int)x >= left;
}

/* MODEL: BOTH GATE-43 basis="DMG semantics: LCDC bit 0 gates BG and window; runs for the DMG profile and compat mode, CGB mode uses ppu_cgb_background" */
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
    if (map_address >= GBB_VRAM_BANK_SIZE) return 0;
    uint8_t tile = m->vram[0][map_address];
    return ppu_tile_color(m, tile, source_y & 7u, source_x & 7u, 0);
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void ppu_begin_object_scan(gbb_instance *m) {
    m->ppu_selected_object_count = 0;
    m->ppu_scan_index = 0;
}

/* Sample one OAM entry every two modeled mode-2 dots. If DMA overlaps that
 * read, this software model treats the candidate as off-screen for the line.
 * The scan-dot placement remains policy, not measured CPU-B timing. */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void ppu_scan_object(gbb_instance *m, unsigned index) {
    if (index >= 40u) return;
    m->ppu_scan_index = (uint8_t)(index + 1u);
    /* Private observer access 9 marks the per-entry mode-2 sample; value 0
     * means DMA suppressed the candidate, value 1 means OAM was sampled. */
    if (m->ly == 0u)
        observe_ppu(m, (uint16_t)(0xFE00u + index), 9,
                    (uint8_t)(m->dma_active ? 0u : 1u));
    /* MODEL: UNKNOWN GATE-44 research:14 -- OAM scan against a DMA in flight; the CGB scan timing question is deferred by D-09/D-12 */
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

/* MODEL: BOTH GATE-45 basis="DMG semantics: object priority by X then OAM index; runs for the DMG profile and compat mode, CGB mode uses ppu_cgb_object" */
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

/* MODEL: BOTH GATE-00 basis=model-neutral */
static uint8_t ppu_palette_shade(uint8_t palette, uint8_t color) {
    return (uint8_t)((palette >> (color * 2u)) & 3u);
}

/* MODEL: BOTH GATE-46 basis="DMG semantics: DMG palette shade composition; runs for the DMG profile and compat mode, CGB mode uses ppu_pixel_cgb" */
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

/* Compat palette default (D-18). One rule: a brightness ramp Y = 31, 21, 11, 1 per shade with
 * R = Y, G = Y - (Y >> 3), B = Y - (Y >> 2), packed as RGB555 (bit 15 clear). The same ramp seeds
 * BG, OBJ0 and OBJ1. These values were authored here without reference to any third-party,
 * boot-ROM or title-hash table (G4); the look is an owner veto item. */
static const uint16_t compat_default_rgb555[3][4] = {
    {0x639Fu, 0x4275u, 0x254Bu, 0x0421u},
    {0x639Fu, 0x4275u, 0x254Bu, 0x0421u},
    {0x639Fu, 0x4275u, 0x254Bu, 0x0421u},
};

/* MODEL: BOTH GATE-00 basis="compat palette lookup; indices are masked so guest bytes cannot leave the table (T-11-34)" */
static uint16_t ppu_compat_resolve(const gbb_instance *m, unsigned set, uint8_t shade) {
    return m->compat_rgb555[set % 3u][shade & 3u];
}

/* MODEL: BOTH GATE-00 basis="compat mode pixel: DMG composition resolved through the compat palette (D-39); never reads vram[1]" */
static uint16_t ppu_pixel_compat(gbb_instance *m, unsigned x) {
    uint8_t background = (m->lcdc & 0x01u) != 0 ? ppu_background_color(m, x) : 0;
    if ((m->lcdc & 0x01u) != 0 && ppu_window_visible_at(m, x))
        m->ppu_window_line_drawn = 1;
    uint8_t object = 0, attributes = 0;
    if (ppu_object_color(m, x, &object, &attributes) &&
        ((attributes & 0x80u) == 0 || background == 0)) {
        const uint8_t palette = (attributes & 0x10u) != 0 ? m->obp1 : m->obp0;
        return ppu_compat_resolve(m, 1u + ((attributes >> 4) & 1u), ppu_palette_shade(palette, object));
    }
    return ppu_compat_resolve(m, 0u, ppu_palette_shade(m->bgp, background));
}

/* ---- CGB-mode colour path (Phase 11, D-01 to D-09) -------------------------------------------------
 * Siblings of the DMG functions above, selected by the single per-dot branch in ppu_transfer_dot.
 * They read only PPU state (VRAM, OAM, CRAM, registers), never the CPU-visible VBK bank. */

/* MODEL: BOTH GATE-00 basis="bank-explicit VRAM read; the renderer never uses vram_bank (D-05, D-36)" */
static uint8_t ppu_vram_read(const gbb_instance *m, unsigned bank, uint16_t address) {
    return address < GBB_VRAM_BANK_SIZE ? m->vram[bank & 1u][address] : 0u;
}

/* One RGB555 colour from a CRAM side. Bit 15 of the stored word is not part of the colour (RESEARCH
 * Correction 10), so a guest word of $FFFF resolves to $7FFF. */
/* MODEL: BOTH GATE-00 basis="pure palette RAM lookup" */
static uint16_t cram_colour(const uint8_t cram[64], unsigned palette, unsigned index) {
    unsigned at = (palette & 7u) * 8u + (index & 3u) * 2u;
    return (uint16_t)((cram[at] | (cram[at + 1u] << 8)) & 0x7FFFu);
}

/* MODEL: BOTH GATE-00 basis="same tile addressing as ppu_tile_color, with an explicit VRAM bank" */
static uint8_t ppu_cgb_tile_color(const gbb_instance *m, uint8_t tile, unsigned bank,
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
    uint8_t low = ppu_vram_read(m, bank, (uint16_t)address);
    uint8_t high = ppu_vram_read(m, bank, (uint16_t)(address + 1u));
    return (uint8_t)(((low >> bit) & 1u) | (((high >> bit) & 1u) << 1));
}

/* MODEL: BOTH GATE-00 basis="CGB mode gates the window on LCDC bit 5 alone; LCDC bit 0 is priority only (D-06)" */
static int ppu_cgb_window_visible_at(const gbb_instance *m, unsigned x) {
    if ((m->lcdc & 0x20u) == 0 || m->ly < m->wy || m->wx > 166u)
        return 0;
    int left = (int)m->wx - 7;
    return (int)x >= left;
}

/* Background or window colour index and its map attribute. The tile index comes from bank 0 and the
 * attribute from bank 1 at the same map address (D-05). Attribute bit 4 is ignored. */
/* MODEL: BOTH GATE-00 basis="CGB mode BG and window fetch with attributes (D-05, D-09)" */
static uint8_t ppu_cgb_background(const gbb_instance *m, unsigned x, uint8_t *attr) {
    int window = ppu_cgb_window_visible_at(m, x);
    unsigned source_x;
    unsigned source_y;
    uint16_t map_base;
    *attr = 0;
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
    if (map_address >= GBB_VRAM_BANK_SIZE) return 0;
    uint8_t tile = ppu_vram_read(m, 0u, map_address);
    uint8_t attributes = ppu_vram_read(m, 1u, map_address);
    unsigned row = source_y & 7u;
    unsigned column = source_x & 7u;
    if ((attributes & 0x40u) != 0) row = 7u - row;
    if ((attributes & 0x20u) != 0) column = 7u - column;
    *attr = attributes;
    return ppu_cgb_tile_color(m, tile, (attributes >> 3) & 1u, row, column, 0);
}

/* First opaque object in ascending OAM index (ppu_scan_object stores them in that order); no X
 * comparison in CGB mode (D-08). OPRI is never read here. */
/* MODEL: BOTH GATE-00 basis="CGB mode object fetch: OAM bit 3 bank, OAM-index order (D-05, D-08)" */
static int ppu_cgb_object(const gbb_instance *m, unsigned x, uint8_t *color, uint8_t *attributes) {
    if ((m->lcdc & 0x02u) == 0) return 0;
    unsigned height = (m->lcdc & 0x04u) != 0 ? 16u : 8u;
    for (unsigned selected = 0; selected < m->ppu_selected_object_count; ++selected) {
        int left = (int)m->ppu_selected_x[selected] - 8;
        int local_x = (int)x - left;
        if (local_x < 0 || local_x >= 8) continue;
        int row = (int)m->ly - ((int)m->ppu_selected_y[selected] - 16);
        if (row < 0 || row >= (int)height) continue;
        uint8_t attrs = m->ppu_selected_attributes[selected];
        if ((attrs & 0x40u) != 0) row = (int)height - 1 - row;
        unsigned tile = m->ppu_selected_tile[selected];
        if (height == 16u) {
            tile &= ~1u;
            tile += (unsigned)row >> 3;
        }
        unsigned source_x = (attrs & 0x20u) != 0 ? 7u - (unsigned)local_x : (unsigned)local_x;
        uint8_t candidate = ppu_cgb_tile_color(m, (uint8_t)tile, (attrs >> 3) & 1u,
                                               (unsigned)row & 7u, source_x, 1);
        if (candidate == 0) continue; /* OBJ colour 0 is transparent before palette lookup. */
        *color = candidate;
        *attributes = attrs;
        return 1;
    }
    return 0;
}

typedef enum { CGB_LAYER_BG, CGB_LAYER_OBJ } cgb_layer;

/* D-07 priority: an opaque object wins unless LCDC.0 = 1, BG colour index is 1-3 and either the
 * OAM priority bit or the BG attribute priority bit is set. */
/* MODEL: BOTH GATE-00 basis="pure CGB mode priority composer (D-07)" */
static cgb_layer ppu_compose_cgb(uint8_t lcdc, uint8_t bg_index, uint8_t bg_attr,
                                 int obj_opaque, uint8_t obj_attr) {
    if (!obj_opaque) return CGB_LAYER_BG;
    if (bg_index == 0u) return CGB_LAYER_OBJ;
    if ((lcdc & 0x01u) == 0) return CGB_LAYER_OBJ;
    if (((obj_attr | bg_attr) & 0x80u) == 0) return CGB_LAYER_OBJ;
    return CGB_LAYER_BG;
}

/* MODEL: BOTH GATE-00 basis="CGB mode pixel: palette RAM resolved per dot (D-01)" */
static uint16_t ppu_pixel_cgb(gbb_instance *m, unsigned x) {
    uint8_t bg_attr = 0;
    uint8_t bg_index = ppu_cgb_background(m, x, &bg_attr);
    if (ppu_cgb_window_visible_at(m, x)) m->ppu_window_line_drawn = 1;
    uint8_t object = 0, object_attr = 0;
    int opaque = ppu_cgb_object(m, x, &object, &object_attr);
    if (ppu_compose_cgb(m->lcdc, bg_index, bg_attr, opaque, object_attr) == CGB_LAYER_OBJ)
        return cram_colour(m->obj_cram, object_attr & 7u, object);
    return cram_colour(m->bg_cram, bg_attr & 7u, bg_index);
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
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

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void ppu_fetcher_step(gbb_instance *m) {
    uint16_t needed = (uint16_t)(GBB_FRAME_WIDTH + m->ppu_fine_scroll);
    if (m->ppu_fetch_enqueued >= needed) return;
    /* MODEL: UNKNOWN GATE-47 research:14 -- fetcher push timing; CGB mode-3 fetcher timing is not claimed and is deferred by D-09/D-12 */
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

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int ppu_window_should_start(const gbb_instance *m) {
    /* MODEL: CGB_ONLY GATE-81 GUARD=model_is_cgb -- CGB mode enables the window by LCDC bit 5 alone, so with LCDC bit 0 clear the window start stall now occurs; CGB mode-3 timing is not claimed (D-09) */
    const unsigned enable_mask = (model_is_cgb(m) && m->exec_mode == GBB_MODE_CGB) ? 0x20u : 0x21u;
    if (m->ppu_window_started || (m->lcdc & enable_mask) != enable_mask ||
        m->ly < m->wy || m->wx > 166u) return 0;
    unsigned start_x = m->wx < 7u ? 0u : (unsigned)m->wx - 7u;
    return m->ppu_output_x == start_x;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
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
        /* MODEL: UNKNOWN GATE-48 research:14 -- object fetch during DMA and its transfer timing; CGB mode-3 stall timing is not claimed and is deferred by D-09/D-12 */
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

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void ppu_transfer_dot(gbb_instance *m) {
    if (m->ppu_transfer_complete) {
        ppu_set_mode(m, 0);
        return;
    }
    ppu_fetcher_step(m);
    /* MODEL: UNKNOWN GATE-49 research:14 -- mode 3 start-up and window stall timing; CGB mode-3 length, WX and window-range differences are not claimed and are deferred by D-09/D-12 */
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
    const unsigned pixel_at = (unsigned)m->ly * GBB_FRAME_WIDTH + fetched_slot;
    if (model_is_dmg(m)) {
        m->frame_working[pixel_at] = ppu_pixel_shade(m, fetched_slot);
    }
    /* MODEL: CGB_ONLY GATE-80 GUARD=model_is_cgb -- CGB mode resolves RGB555 per dot against live CRAM into rgb_working (D-01, D-02); compat mode is routed by plan 11-04 */
    else if (model_is_cgb(m) && m->exec_mode == GBB_MODE_CGB) {
        m->rgb_working[pixel_at] = ppu_pixel_cgb(m, fetched_slot);
    }
    /* MODEL: CGB_ONLY GATE-82 GUARD=model_is_cgb -- compat mode (DMG software on the CGB profile) resolves DMG shades through the instance compat palette into rgb_working (D-17, D-39) */
    else if (model_is_cgb(m)) {
        m->rgb_working[pixel_at] = ppu_pixel_compat(m, fetched_slot);
    }
    if (++m->ppu_output_x == GBB_FRAME_WIDTH) m->ppu_transfer_complete = 1;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void ppu_advance_dot(gbb_instance *m) {
    if ((m->lcdc & 0x80u) == 0) return;
    /* MODEL: UNKNOWN GATE-50 research:14 -- line length and LY timing; CGB line-edge timing is unresearched and deferred by D-09/D-12 */
    if (m->ppu_dot < GBB_DOTS_PER_LINE - 1u) {
        ++m->ppu_dot;
    } else {
        if (m->ly < GBB_FRAME_HEIGHT && m->ppu_window_line_drawn &&
            m->ppu_window_line != UINT8_MAX)
            ++m->ppu_window_line;
        m->ppu_dot = 0;
        ++m->ly;
        if (m->ly == GBB_LINES_PER_FRAME) {
            m->ly = 0;
            m->ppu_window_line = 0;
        }
        observe_ppu(m, 0xFF44, 6, m->ly);
        m->ppu_window_line_drawn = 0;
        m->ppu_transfer_complete = 0;
        if (m->ly < GBB_FRAME_HEIGHT) ppu_begin_object_scan(m);
        if (m->ly == GBB_FRAME_HEIGHT) {
            memcpy(m->frame_completed, m->frame_working, sizeof(m->frame_completed));
            /* MODEL: CGB_ONLY GATE-79 GUARD=model_is_cgb -- the RGB frame completes together with the shade frame (D-02) */
            if (model_is_cgb(m))
                memcpy(m->rgb_completed, m->rgb_working, sizeof(m->rgb_completed));
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
        if (m->ppu_dot != 0u && (m->ppu_dot & 1u) == 0u)
            ppu_scan_object(m, m->ppu_scan_index);
    } else if (m->ppu_dot == 80u) {
        /* The per-dot cadence above samples entries 0-38 at dots 2-78.
         * Complete the 40-entry OAM scan at the mode-2 boundary before
         * mode 3 begins. This keeps scan ordering explicit and avoids
         * deriving an unsigned index from dot zero on line wrap. */
        if (m->ppu_scan_index < 40u)
            ppu_scan_object(m, m->ppu_scan_index);
        ppu_begin_transfer(m);
        ppu_set_mode(m, 3);
    } else if (m->ppu_mode == 3u) {
        ppu_transfer_dot(m);
    }
}

/* OAM DMA source map (D-16). The DMG envelope is frozen (D-024): VRAM and WRAM are read and every other
 * page, including ROM, cartridge RAM and E0-FF, reads $FF. The CGB profile (both modes) reads ROM and
 * cartridge RAM through cart_read, VRAM from the selected bank, WRAM through the banked helper, and
 * E0-FF as $FF. The cartridge and E0-FF cells are PANDOCS or ORACLE_SAMEBOY claims and are not
 * hardware-verified for CGB-E (see docs/cgb-profile.md). */
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static uint8_t dma_source_read(const gbb_instance *m, uint16_t address) {
    /* MODEL: CGB_ONLY GATE-51 GUARD=model_is_cgb -- OAM DMA reads the cartridge and the banked VRAM and WRAM on the CGB profile */
    if (model_is_cgb(m)) {
        if (address < 0x8000u || (address >= 0xA000u && address <= 0xBFFFu))
            return cart_read(m, address);
        if (address >= 0x8000u && address <= 0x9FFFu)
            return m->vram[m->vram_bank][address - 0x8000u];
        if (address >= 0xC000u && address <= 0xDFFFu)
            return *wram_byte(m, address);
        return 0xFFu;
    }
    /* MODEL: DMG_ONLY GATE-75 GUARD=model_is_dmg -- the DMG source map is VRAM and WRAM only; everything else reads $FF (D-024) */
    if (model_is_dmg(m)) {
        if (address >= 0x8000u && address <= 0x9FFFu)
            return m->vram[m->vram_bank][address - 0x8000u];
        if (address >= 0xC000u && address <= 0xDFFFu)
            return *wram_byte(m, address);
    }
    return 0xFFu;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void dma_start(gbb_instance *m) {
    /* MODEL: UNKNOWN GATE-52 expected-failure:cgb-dma-restart-oracle-only -- DMA restart timing has no CGB oracle */
    m->dma_page = m->dma_pending_page;
    m->dma_index = 0;
    m->dma_phase = 0;
    m->dma_active = 1;
    m->dma_cpu_blocked = 0;
    m->dma_start_pending = 0;
    observe_dma(m, 0xFF46u, 1, m->dma_page);
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void dma_advance_half_dot(gbb_instance *m) {
    if (!m->dma_active) return;
    /* MODEL: BOTH GATE-53 basis="OAM DMA byte period is measured in CPU ticks and remains common across profiles, D-10" -- DMA byte period */
    if (++m->dma_phase < GBB_T_PER_M) return;
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

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void apu_sequencer_clock(gbb_instance *m) {
    if (!m->apu_power) return;
    const uint8_t step = m->apu_sequencer_step;
    if ((step & 1u) == 0u) {
        for (unsigned i = 0u; i < 2u; ++i) {
            apu_pulse_channel *pulse = &m->apu_pulse[i];
            if ((pulse->control & 0x40u) != 0u && pulse->length != 0u &&
                --pulse->length == 0u) pulse->enabled = 0;
        }
        if ((m->apu_wave.control & 0x40u) != 0u && m->apu_wave.length != 0u &&
            --m->apu_wave.length == 0u) m->apu_wave.enabled = 0;
        if ((m->apu_noise.control & 0x40u) != 0u && m->apu_noise.length != 0u &&
            --m->apu_noise.length == 0u) m->apu_noise.enabled = 0;
    }
    if (step == 2u || step == 6u) {
        apu_pulse_channel *pulse = &m->apu_pulse[0];
        const uint8_t period = (uint8_t)((pulse->sweep >> 4) & 7u);
        if (pulse->sweep_timer != 0u && --pulse->sweep_timer == 0u) {
            pulse->sweep_timer = period == 0u ? 8u : period;
            if (pulse->sweep_enabled && period != 0u) {
                const uint8_t shift = (uint8_t)(pulse->sweep & 7u);
                if (shift != 0u) {
                    const int32_t delta = (int32_t)(pulse->sweep_shadow >> shift);
                    int32_t next;
                    if ((pulse->sweep & 8u) != 0u) {
                        pulse->sweep_negate_used = 1;
                        next = (int32_t)pulse->sweep_shadow - delta;
                    } else {
                        next = (int32_t)pulse->sweep_shadow + delta;
                    }
                    if (next > 2047 || next < 0) pulse->enabled = 0;
                    else {
                        pulse->sweep_shadow = (uint16_t)next;
                        pulse->frequency = (uint16_t)next;
                        pulse->frequency_low = (uint8_t)next;
                        pulse->control = (uint8_t)((pulse->control & 0x40u) | ((uint16_t)next >> 8));
                        pulse->timer = (uint16_t)((2048u - (uint16_t)next) * 64u);
                        if (next + ((uint16_t)next >> shift) > 2047) pulse->enabled = 0;
                    }
                }
            }
        }
    }
    if (step == 7u) {
        for (unsigned i = 0u; i < 2u; ++i) {
            apu_pulse_channel *pulse = &m->apu_pulse[i];
            const uint8_t period = (uint8_t)(pulse->envelope & 7u);
            if (period != 0u && pulse->envelope_timer != 0u &&
                --pulse->envelope_timer == 0u) {
                pulse->envelope_timer = period;
                if ((pulse->envelope & 8u) != 0u) {
                    if (pulse->volume < 15u) ++pulse->volume;
                } else if (pulse->volume > 0u) --pulse->volume;
            }
        }
        const uint8_t noise_period = (uint8_t)(m->apu_noise.envelope & 7u);
        if (noise_period != 0u && m->apu_noise.envelope_timer != 0u &&
            --m->apu_noise.envelope_timer == 0u) {
            m->apu_noise.envelope_timer = noise_period;
            if ((m->apu_noise.envelope & 8u) != 0u) {
                if (m->apu_noise.volume < 15u) ++m->apu_noise.volume;
            } else if (m->apu_noise.volume > 0u) --m->apu_noise.volume;
        }
    }
    m->apu_sequencer_step = (uint8_t)((step + 1u) & 7u);
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static void advance_devices_to(gbb_instance *m, uint64_t target) {
    while (m->time_half_dots < target) {
        ++m->time_half_dots;
        apply_input_events_now(m);
        /* MODEL: CGB_ONLY GATE-90 GUARD=double_speed -- CPU-side timers, serial and OAM DMA use cpu_ticks scaling */
        if (!m->double_speed) m->divider_phase ^= 1u;
        const int cpu_tick = m->double_speed || m->divider_phase == 0u; /* P12-M3 */
        /* MODEL: UNKNOWN GATE-54 research:14 -- timer reload and IF delay */
        if (cpu_tick && m->timer_reload_pending && m->timer_reload_remaining != 0 &&
            --m->timer_reload_remaining == 0) {
            m->tima = m->tma;
            m->timer_reload_pending = 0;
            m->timer_reloaded_at = m->time_half_dots;
            m->interrupt_flags |= 0x04u;
            observe_bus(m, 0, 0xFF05, 3, m->tima);
            observe_bus(m, 0, 0xFF0F, 3, (uint8_t)(0xE0u | m->interrupt_flags));
            diagnostic_add(m, GBB_DIAGNOSTIC_TIMER, m->time_half_dots, 0xFF05, m->tima);
        }
        /* MODEL: UNKNOWN GATE-55 research:14 -- serial internal clock rate */
        if (cpu_tick && m->serial_active && (m->serial_control & 1u) != 0 &&
            m->serial_edge_remaining != 0 && --m->serial_edge_remaining == 0) { /* P12-M2 */
            m->serial_data = (uint8_t)((m->serial_data << 1) | 1u);
            if (++m->serial_bits == 8u) {
                m->serial_active = 0;
                m->serial_control &= 1u;
                m->interrupt_flags |= 0x08u;
            } else {
                m->serial_edge_remaining = 512u;
            }
        }
        if (cpu_tick) {
            /* MODEL: CGB_ONLY GATE-56 GUARD=double_speed -- CGB APU frame sequencer follows the selected DIV tap, D-11 */
            const uint16_t tap = m->double_speed ? 0x2000u : 0x1000u; /* P12-M4 */
            const int apu_signal_before = (m->divider_counter & tap) != 0u;
            ++m->divider_counter;
            m->div = (uint8_t)(m->divider_counter >> 8);
            timer_set_signal(m, timer_input(m), m->time_half_dots);
            if (apu_signal_before && (m->divider_counter & tap) == 0u)
                apu_sequencer_clock(m);
        }
        for (unsigned i = 0u; i < 2u; ++i) {
            apu_pulse_channel *pulse = &m->apu_pulse[i];
            if (pulse->enabled) {
                if (pulse->timer > 1u) --pulse->timer; /* P12-M17 */
                else {
                    pulse->timer = (uint16_t)((2048u - pulse->frequency) * 64u);
                    pulse->phase = (uint8_t)((pulse->phase + 1u) & 7u);
                }
            }
        }
        if (m->apu_wave.enabled) {
            if (m->apu_wave.timer > 1u) --m->apu_wave.timer;
            else {
                uint16_t frequency = (uint16_t)(m->apu_wave.frequency_low |
                                                ((m->apu_wave.control & 7u) << 8));
                m->apu_wave.timer = (uint16_t)((2048u - frequency) * 2u);
                m->apu_wave.position = (uint8_t)((m->apu_wave.position + 1u) & 31u);
            }
        }
        if (m->apu_noise.enabled) {
            if (m->apu_noise.timer > 1u) --m->apu_noise.timer;
            else {
                m->apu_noise.timer = apu_noise_period(&m->apu_noise);
                uint16_t feedback = (uint16_t)((m->apu_noise.lfsr ^
                                                (m->apu_noise.lfsr >> 1)) & 1u);
                m->apu_noise.lfsr = (uint16_t)((m->apu_noise.lfsr >> 1) |
                                               (feedback << 14));
                if ((m->apu_noise.polynomial & 8u) != 0u)
                    m->apu_noise.lfsr = (uint16_t)((m->apu_noise.lfsr & ~(uint16_t)0x40u) |
                                                   (feedback << 6));
            }
        }
        m->apu_sample_phase += GBB_AUDIO_SAMPLE_RATE;
        int32_t left, right;
        audio_current_mix(m, &left, &right);
        if (left != m->audio_mix_level[0] || right != m->audio_mix_level[1]) {
            const unsigned phase = (unsigned)((m->apu_sample_phase * GBB_AUDIO_EVENT_PHASES) /
                                               GBB_AUDIO_CLOCK_HALF_DOTS) % GBB_AUDIO_EVENT_PHASES;
            audio_add_edge(m, 0u, left - m->audio_mix_level[0], phase);
            audio_add_edge(m, 1u, right - m->audio_mix_level[1], phase);
            m->audio_mix_level[0] = left; m->audio_mix_level[1] = right;
        }
        if (m->apu_sample_phase >= GBB_AUDIO_CLOCK_HALF_DOTS) {
            m->apu_sample_phase -= GBB_AUDIO_CLOCK_HALF_DOTS;
            const gbb_audio_frame frame = audio_process_sample(m);
            if (m->audio_frames != NULL &&
                m->audio_frame_count < m->audio_frame_capacity)
                m->audio_frames[m->audio_frame_count++] = frame;
        }
        if (GBB_P13_MUT(52)) hdma_advance_half_dot(m); /* P13-05-M13: shifted collision order */
        if (cpu_tick) dma_advance_half_dot(m); /* P12-M14 */
        if (!GBB_P13_MUT(52))
            hdma_advance_half_dot(m); /* P13-M1: OAM retains precedence; HDMA commits before PPU advancement. */
        m->ppu_half_phase ^= 1u; /* P12-M1 */
        if (m->ppu_half_phase == 0) ppu_advance_dot(m);
    }
}

/* MODEL: BOTH GATE-00 basis=host-api */
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

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
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
    /* MODEL: DMG_ONLY GATE-57 GUARD=model_is_dmg -- frame output is DMG shades only; the CGB profile has no colour output yet (D-05) */
    if (!model_is_dmg(instance)) return GBB_UNSUPPORTED_PROFILE;
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

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
gbb_error gbb_copy_frame_rgb555(const gbb_instance *instance, uint16_t *pixels,
                                size_t capacity_bytes, size_t pitch_bytes,
                                gbb_frame_info *out_info) {
    const size_t row_bytes = (size_t)GBB_FRAME_WIDTH * 2u;
    if (instance == NULL || pixels == NULL || out_info == NULL) return GBB_INVALID_ARGUMENT;
    /* uint16_t stores need 2-byte alignment and a whole-pixel stride (T-11-14). */
    if (((uintptr_t)(void *)pixels & 1u) != 0u || (pitch_bytes & 1u) != 0u)
        return GBB_INVALID_ARGUMENT;
    if (pitch_bytes < row_bytes ||
        pitch_bytes > (SIZE_MAX - row_bytes) / (GBB_FRAME_HEIGHT - 1u))
        return GBB_INVALID_ARGUMENT;
    size_t required = (GBB_FRAME_HEIGHT - 1u) * pitch_bytes + row_bytes;
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
    /* MODEL: CGB_ONLY GATE-83 GUARD=model_is_cgb -- colour frames are CGB-profile only; the DMG profile returns GBB_UNSUPPORTED_PROFILE (D-15), symmetric with GATE-57 */
    if (!model_is_cgb(instance)) return GBB_UNSUPPORTED_PROFILE;
    if (instance->frame_generation == 0) return GBB_FRAME_NOT_READY;
    for (size_t y = 0; y < GBB_FRAME_HEIGHT; ++y)
        memcpy((uint8_t *)pixels + y * pitch_bytes,
               instance->rgb_completed + y * GBB_FRAME_WIDTH, row_bytes);
    gbb_frame_info info = {GBB_FRAME_WIDTH, GBB_FRAME_HEIGHT,
                           instance->frame_generation,
                           instance->frame_completion_half_dots};
    *out_info = info;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_set_compat_palette(gbb_instance *instance, const gbb_compat_palette *palette) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    if (palette == NULL) {
        memcpy(instance->compat_rgb555, compat_default_rgb555, sizeof(instance->compat_rgb555));
        return GBB_OK;
    }
    if (palette->struct_size < GBB_COMPAT_PALETTE_SIZE_V1) return GBB_INVALID_ARGUMENT;
    /* Validate every entry before the first store so a rejected set mutates nothing (T-11-12). */
    for (unsigned i = 0; i < 4u; ++i)
        if (((palette->bg[i] | palette->obj0[i] | palette->obj1[i]) & 0x8000u) != 0u)
            return GBB_INVALID_ARGUMENT;
    for (unsigned i = 0; i < 4u; ++i) {
        instance->compat_rgb555[0][i] = palette->bg[i];
        instance->compat_rgb555[1][i] = palette->obj0[i];
        instance->compat_rgb555[2][i] = palette->obj1[i];
    }
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_get_compat_palette(const gbb_instance *instance, gbb_compat_palette *out_palette) {
    if (instance == NULL || out_palette == NULL ||
        out_palette->struct_size < GBB_COMPAT_PALETTE_SIZE_V1)
        return GBB_INVALID_ARGUMENT;
    /* Field by field: the caller's struct may be larger than V1 and keeps its extra bytes. */
    for (unsigned i = 0; i < 4u; ++i) {
        out_palette->bg[i] = instance->compat_rgb555[0][i];
        out_palette->obj0[i] = instance->compat_rgb555[1][i];
        out_palette->obj1[i] = instance->compat_rgb555[2][i];
    }
    out_palette->struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-side-mixing */
static int audio_preflight(const gbb_instance *m, uint64_t half_dots) {
    if (!m->audio_run_active) return 1;
    const uint64_t samples = (m->apu_sample_phase +
        half_dots * GBB_AUDIO_SAMPLE_RATE) / GBB_AUDIO_CLOCK_HALF_DOTS;
    return samples <= (uint64_t)(m->audio_frame_capacity - m->audio_frame_count);
}

/* MODEL: BOTH GATE-00 basis=model-neutral */
static void advance_devices(gbb_instance *m, uint64_t half_dots) {
    advance_devices_to(m, m->time_half_dots + half_dots);
}
/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void set_hl(gbb_instance *m, uint16_t value) { m->h = (uint8_t)(value >> 8); m->l = (uint8_t)value; }

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static int recognized_mbc1m_candidate(const uint8_t *rom, size_t size) {
    static const uint8_t nintendo_logo[48] = {
        0xCEu, 0xEDu, 0x66u, 0x66u, 0xCCu, 0x0Du, 0x00u, 0x0Bu,
        0x03u, 0x73u, 0x00u, 0x83u, 0x00u, 0x0Cu, 0x00u, 0x0Du,
        0x00u, 0x08u, 0x11u, 0x1Fu, 0x88u, 0x89u, 0x00u, 0x0Eu,
        0xDCu, 0xCCu, 0x6Eu, 0xE6u, 0xDDu, 0xDDu, 0xD9u, 0x99u,
        0xBBu, 0xBBu, 0x67u, 0x63u, 0x6Eu, 0x0Eu, 0xECu, 0xCCu,
        0xDDu, 0xDCu, 0x99u, 0x9Fu, 0xBBu, 0xB9u, 0x33u, 0x3Eu
    };
    const size_t bank = 0x10u * 0x4000u;
    if (size < bank + 0x150u ||
        memcmp(rom + bank + 0x104u, nintendo_logo, sizeof(nintendo_logo)) != 0)
        return 0;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[bank + i] - 1u);
    return checksum == rom[bank + 0x14Du] &&
           rom[bank + 0x147u] >= 0x01u && rom[bank + 0x147u] <= 0x03u;
}

/* $143 classification (D-03). Hardware decodes CGB mode from bit 7 and PGB mode from bits 2-3;
 * the $C0 convention is ignored by hardware but reported so callers can see it. */
/* MODEL: BOTH GATE-00 basis=header-byte-143 */
static uint8_t cgb_support_of(uint8_t flag) {
    if ((flag & 0x80u) == 0u) return GBB_CGB_SUPPORT_NONE;
    if ((flag & 0x0Cu) != 0u) return GBB_CGB_SUPPORT_PGB;
    if (flag == 0x80u) return GBB_CGB_SUPPORT_ENHANCED;
    if (flag == 0xC0u) return GBB_CGB_SUPPORT_ONLY;
    return GBB_CGB_SUPPORT_OTHER;
}

/* MODEL: BOTH GATE-00 basis=D-24 */
static gbb_error validate_header(gbb_profile profile, const uint8_t *rom, size_t size,
                                 cartridge_info *out_info) {
    if (rom == NULL || size == 0) return GBB_INVALID_ARGUMENT;
    if (size < 0x150) return GBB_ROM_TRUNCATED;
    const uint8_t type = rom[0x147];
    const uint8_t rom_size_code = rom[0x148];
    const uint8_t ram_size_code = rom[0x149];
    const cart_type_row *row = cart_row_for_type(type);
    const size_t ceiling =
        row != NULL ? row->early_ceiling_bytes : GBB_LEGACY_MAX_ROM_SIZE;
    if (size > ceiling) return GBB_ROM_TOO_LARGE;
    if (row == NULL) return GBB_UNSUPPORTED_CARTRIDGE;
    /* Reject the code before the shift below: it must never exceed the row. */
    if (rom_size_code > row->max_rom_code) return GBB_UNSUPPORTED_ROM_SIZE;

    size_t ram_size = 0u;
    int mbc30_ram_marker = 0;
    if (row->ram_rule == CART_RAM_NONE) {
        if (ram_size_code != 0u) return GBB_UNSUPPORTED_RAM_SIZE;
    } else if (row->ram_rule == CART_RAM_MBC2) {
        /* The 512 bytes come from the type row; $149 must not claim more. */
        if (ram_size_code != 0u) return GBB_UNSUPPORTED_RAM_SIZE;
        ram_size = MBC2_RAM_BYTES;
    } else if (row->ram_rule == CART_RAM_MBC3) {
        /* $05 (64 KiB, MBC30) is never loadable: it is remembered and answered as
         * a variant only after the length and checksum checks pass (Phase 9 D-02). */
        switch (ram_size_code) {
        case 0x02u: ram_size = 8192u; break;
        case 0x03u: ram_size = 32768u; break;
        case 0x05u: mbc30_ram_marker = 1; break;
        default: return GBB_UNSUPPORTED_RAM_SIZE;
        }
    } else if (row->ram_rule == CART_RAM_MBC5) {
        switch (ram_size_code) {
        case 0x02u: ram_size = 8192u; break;
        case 0x03u: ram_size = 32768u; break;
        case 0x05u: ram_size = 65536u; break;
        case 0x04u: ram_size = 131072u; break;
        default: return GBB_UNSUPPORTED_RAM_SIZE;
        }
    } else if (ram_size_code == 0x02u) {
        ram_size = 8192u;
    } else if (ram_size_code == 0x03u && rom_size_code <= row->ram32_max_rom_code) {
        ram_size = 32768u;
    } else {
        return GBB_UNSUPPORTED_RAM_SIZE;
    }

    const size_t declared = (size_t)32768u << rom_size_code;
    if (size < declared) return GBB_ROM_TRUNCATED;
    if (size != declared) return GBB_ROM_SIZE_MISMATCH;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    /* MODEL: BOTH GATE-58 basis=D-24 -- header and checksum validation is profile-independent */
    if (checksum != rom[0x14D]) return GBB_INVALID_ROM;
    if (row->kind == CART_MBC1 && declared >= 512u * 1024u &&
        recognized_mbc1m_candidate(rom, size))
        return GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
    /* MBC30 (ROM code $07 or 64 KiB RAM) has an undocumented register layout here. */
    if (row->kind == CART_MBC3 && (rom_size_code == 0x07u || mbc30_ram_marker))
        return GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
    const uint8_t cgb_flag = rom[0x143];
    const uint8_t cgb_support = cgb_support_of(cgb_flag);
    /* MODEL: CGB_ONLY GATE-67 GUARD=GBB_PROFILE_CGB_CPU_E -- a PGB-flagged $143 is rejected on the CGB profile instead of running in a mode the hardware would not enter (D-03) */
    if (profile == GBB_PROFILE_CGB_CPU_E && cgb_support == GBB_CGB_SUPPORT_PGB)
        return GBB_UNSUPPORTED_EXECUTION_MODE;
    if (out_info != NULL) {
        out_info->cgb_flag = cgb_flag;
        out_info->cgb_support = cgb_support;
        out_info->type = type;
        out_info->kind = row->kind;
        out_info->ram_window_mapped = row->ram_window_mapped;
        out_info->has_battery = row->has_battery;
        out_info->has_timer = row->has_timer;
        out_info->has_rumble = row->has_rumble;
        out_info->ram_size = ram_size;
    }
    return GBB_OK;
}

/* Execution mode is a property of profile plus $143 (D-03): the DMG profile ignores $143, the
 * CGB profile runs CGB mode when bit 7 is set and DMG compatibility mode otherwise. */
/* MODEL: BOTH GATE-00 basis=header-byte-143 */
static uint8_t exec_mode_for(int cgb_profile, uint8_t cgb_flag) {
    if (!cgb_profile) return GBB_MODE_DMG;
    return (cgb_flag & 0x80u) != 0u ? GBB_MODE_CGB : GBB_MODE_CGB_DMG_COMPAT;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance) {
    if (out_instance == NULL) return GBB_INVALID_ARGUMENT;
    *out_instance = NULL;
    /* MODEL: BOTH GATE-59 basis=profile-argument-validated -- the switch accepts exactly the two implemented profiles (D-01) */
    switch (profile) {
    case GBB_PROFILE_DMG_CPU_B:
    case GBB_PROFILE_CGB_CPU_E:
        break;
    default:
        return GBB_UNSUPPORTED_PROFILE;
    }
    gbb_instance *m = calloc(1, sizeof(*m));
    if (m == NULL) return GBB_OUT_OF_MEMORY;
    m->profile = (uint8_t)profile;
    m->exec_mode = GBB_MODE_NONE;
    memcpy(m->compat_rgb555, compat_default_rgb555, sizeof(m->compat_rgb555));
    reset_state(m); /* RAM fill is emulator policy; hardware power-on RAM is unspecified. */
    *out_instance = m;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-api */
void gbb_destroy(gbb_instance *instance) {
    if (instance != NULL) {
        free(instance->rom);
        free(instance->cartridge_ram);
        free(instance);
    }
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_reset(gbb_instance *instance) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    /* Reset drops the motor line; only a line that was on is a transition.
     * Loads and gbb_create never reach this, so they never count a change. */
    if (instance->cart.rumble_on) {
        instance->cart.rumble_on = 0u;
        if (instance->cart.rumble_changes != UINT64_MAX) ++instance->cart.rumble_changes;
    }
    /* D-09: the clock keeps running across a reset. Bank the elapsed time, let
     * reset_state zero time_half_dots, then rebase the anchor to match. */
    if (instance->cart.has_timer) rtc_sync(&instance->cart, instance->time_half_dots);
    reset_state(instance);
    if (instance->cart.has_timer) instance->cart.rtc_synced_at = 0u;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    cartridge_info info = {0};
    gbb_error validation = validate_header((gbb_profile)instance->profile, rom, rom_size, &info);
    if (validation != GBB_OK) return validation;
    uint8_t *copy = malloc(rom_size);
    if (copy == NULL) return GBB_OUT_OF_MEMORY;
    memcpy(copy, rom, rom_size);
    uint8_t *new_ram = NULL;
    if (info.ram_size != 0u) {
        new_ram = malloc(info.ram_size);
        if (new_ram == NULL) {
            free(copy);
            return GBB_OUT_OF_MEMORY;
        }
        memset(new_ram, 0xFF, info.ram_size);
    }
    free(instance->rom);
    free(instance->cartridge_ram);
    instance->rom = copy;
    instance->rom_size = rom_size;
    instance->cartridge_ram = new_ram;
    instance->cartridge_ram_size = info.ram_size;
    instance->battery_generation = 0u;
    memset(&instance->cart, 0, sizeof(instance->cart));
    instance->cart.kind = info.kind;
    instance->cart.ram_window_mapped = info.ram_window_mapped;
    instance->cart.has_battery = info.has_battery;
    instance->cart.has_timer = info.has_timer;
    instance->cart.has_rumble = info.has_rumble;
    /* The mode commits here, after both allocations, so a failed load leaves it unchanged. */
    instance->exec_mode = exec_mode_for(model_is_cgb(instance), info.cgb_flag);
    instance->cgb_flag = info.cgb_flag;
    instance->cgb_support = info.cgb_support;
    instance->cartridge_type = info.type;
    reset_state(instance);
    instance->loaded = 1;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-api */
static void info_store(gbb_info *out, const gbb_info *src) {
    /* Field by field, never a struct copy: the caller's struct may be larger than V1 and its
     * extra bytes stay untouched. The V1 floor was checked, so every field below fits. */
    out->profile = src->profile;
    out->mode = src->mode;
    out->flags = src->flags;
    out->cgb_flag = src->cgb_flag;
    out->cgb_support = src->cgb_support;
    out->cartridge_type = src->cartridge_type;
    out->reserved0 = 0u;
    out->rom_size_bytes = src->rom_size_bytes;
    out->ram_size_bytes = src->ram_size_bytes;
    out->struct_size = GBB_INFO_SIZE_V1;
}

/* MODEL: BOTH GATE-00 basis=host-api */
static uint32_t info_flags(int profile_is_dmg, uint8_t cgb_support, int battery, int timer,
                           int rumble) {
    uint32_t flags = GBB_INFO_HAS_ROM;
    if (profile_is_dmg && cgb_support == GBB_CGB_SUPPORT_ONLY) flags |= GBB_INFO_CGB_ONLY_ON_DMG;
    if (battery) flags |= GBB_INFO_HAS_BATTERY;
    if (timer) flags |= GBB_INFO_HAS_RTC;
    if (rumble) flags |= GBB_INFO_HAS_RUMBLE;
    return flags;
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_probe_rom(gbb_profile profile, const uint8_t *rom, size_t rom_size,
                        gbb_info *out_info) {
    if (profile != GBB_PROFILE_DMG_CPU_B && profile != GBB_PROFILE_CGB_CPU_E)
        return GBB_UNSUPPORTED_PROFILE;
    if (out_info == NULL || (rom == NULL && rom_size != 0u) ||
        out_info->struct_size < GBB_INFO_SIZE_V1)
        return GBB_INVALID_ARGUMENT;
    cartridge_info cart = {0};
    gbb_error validation = validate_header(profile, rom, rom_size, &cart);
    if (validation != GBB_OK) return validation;
    gbb_info info = {0};
    info.profile = (uint32_t)profile;
    info.mode = exec_mode_for(profile == GBB_PROFILE_CGB_CPU_E, cart.cgb_flag);
    info.flags = info_flags(profile == GBB_PROFILE_DMG_CPU_B, cart.cgb_support,
                            cart.has_battery, cart.has_timer, cart.has_rumble);
    info.cgb_flag = cart.cgb_flag;
    info.cgb_support = cart.cgb_support;
    info.cartridge_type = cart.type;
    info.rom_size_bytes = (uint32_t)rom_size; /* validated <= 8 MiB */
    info.ram_size_bytes = (uint32_t)cart.ram_size;
    info_store(out_info, &info);
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_get_info(const gbb_instance *instance, gbb_info *out_info) {
    if (instance == NULL || out_info == NULL || out_info->struct_size < GBB_INFO_SIZE_V1)
        return GBB_INVALID_ARGUMENT;
    gbb_info info = {0};
    info.profile = instance->profile;
    if (instance->loaded) {
        info.mode = instance->exec_mode;
        info.flags = info_flags(model_is_dmg(instance), instance->cgb_support,
                                instance->cart.has_battery, instance->cart.has_timer,
                                instance->cart.has_rumble);
        info.cgb_flag = instance->cgb_flag;
        info.cgb_support = instance->cgb_support;
        info.cartridge_type = instance->cartridge_type;
        info.rom_size_bytes = (uint32_t)instance->rom_size;
        info.ram_size_bytes = (uint32_t)instance->cartridge_ram_size;
    }
    info_store(out_info, &info);
    return GBB_OK;
}

/* A timer cartridge is battery-backed even when it has no RAM ($0F): its image
 * is the RTC block alone. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static int has_battery_image(const gbb_instance *instance) {
    return instance != NULL && instance->loaded && instance->cart.has_battery &&
           (instance->cartridge_ram_size != 0u || instance->cart.has_timer);
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static size_t battery_image_size(const gbb_instance *instance) {
    return instance->cartridge_ram_size +
           (instance->cart.has_timer ? (size_t)GBB_RTC_BLOCK_SIZE : 0u);
}

/* RTC block v1 (D-16), written field by field so no struct layout leaks:
 *   0-3 "GBRT", 4 version, 5-8 sub (u32 LE), 9-13 live S M H DL DH,
 *   14-18 latched S M H DL DH, 19 latch_prev, 20 reserved zero. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static void rtc_block_write(const cart_state *c, uint8_t out[GBB_RTC_BLOCK_SIZE]) {
    out[0] = 'G'; out[1] = 'B'; out[2] = 'R'; out[3] = 'T';
    out[4] = 1u;
    out[5] = (uint8_t)(c->rtc_sub & 0xFFu);
    out[6] = (uint8_t)((c->rtc_sub >> 8) & 0xFFu);
    out[7] = (uint8_t)((c->rtc_sub >> 16) & 0xFFu);
    out[8] = (uint8_t)((c->rtc_sub >> 24) & 0xFFu);
    out[9] = c->rtc_s; out[10] = c->rtc_m; out[11] = c->rtc_h;
    out[12] = c->rtc_dl; out[13] = c->rtc_dh;
    for (unsigned i = 0u; i < 5u; ++i) out[14u + i] = c->rtc_l[i];
    out[19] = c->rtc_latch_prev;
    out[20] = 0u;
}

/* Validates every field before storing any of them; out is written only on
 * success. Out-of-range-but-legal values (S = 63, H = 31) are accepted because
 * a guest can store them. */
/* MODEL: BOTH GATE-00 basis=cartridge-side */
static gbb_error rtc_block_parse(const uint8_t in[GBB_RTC_BLOCK_SIZE], cart_state *out) {
    if (in[0] != 'G' || in[1] != 'B' || in[2] != 'R' || in[3] != 'T') return GBB_INVALID_ARGUMENT;
    if (in[4] != 1u) return GBB_INVALID_ARGUMENT;
    const uint32_t sub = (uint32_t)in[5] | ((uint32_t)in[6] << 8) |
                         ((uint32_t)in[7] << 16) | ((uint32_t)in[8] << 24);
    if (sub > RTC_SUB_MASK) return GBB_INVALID_ARGUMENT;
    for (unsigned copy = 0u; copy < 2u; ++copy) {
        const uint8_t *r = in + 9u + copy * 5u;
        if (r[0] > 0x3Fu || r[1] > 0x3Fu || r[2] > 0x1Fu) return GBB_INVALID_ARGUMENT;
        if ((r[4] & 0x3Eu) != 0u) return GBB_INVALID_ARGUMENT;
    }
    if (in[20] != 0u) return GBB_INVALID_ARGUMENT;
    out->rtc_sub = sub;
    out->rtc_s = in[9]; out->rtc_m = in[10]; out->rtc_h = in[11];
    out->rtc_dl = in[12]; out->rtc_dh = in[13];
    for (unsigned i = 0u; i < 5u; ++i) out->rtc_l[i] = in[14u + i];
    out->rtc_latch_prev = in[19];
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
static int rtc_fields_equal(const cart_state *a, const cart_state *b) {
    return a->rtc_sub == b->rtc_sub && a->rtc_s == b->rtc_s && a->rtc_m == b->rtc_m &&
           a->rtc_h == b->rtc_h && a->rtc_dl == b->rtc_dl && a->rtc_dh == b->rtc_dh &&
           memcmp(a->rtc_l, b->rtc_l, 5u) == 0 && a->rtc_latch_prev == b->rtc_latch_prev;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
gbb_error gbb_battery_size(const gbb_instance *instance, size_t *out_size) {
    if (instance == NULL || out_size == NULL) return GBB_INVALID_ARGUMENT;
    if (!has_battery_image(instance)) return GBB_NO_BATTERY;
    *out_size = battery_image_size(instance);
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
gbb_error gbb_copy_battery(const gbb_instance *instance, uint8_t *out_bytes,
                           size_t capacity_bytes) {
    if (instance == NULL || out_bytes == NULL) return GBB_INVALID_ARGUMENT;
    if (!has_battery_image(instance)) return GBB_NO_BATTERY;
    if (capacity_bytes < battery_image_size(instance)) return GBB_BUFFER_TOO_SMALL;
    if (instance->cartridge_ram_size != 0u)
        memcpy(out_bytes, instance->cartridge_ram, instance->cartridge_ram_size);
    if (instance->cart.has_timer) {
        /* Project the clock to now on a local copy; the instance stays const. */
        cart_state projected = instance->cart;
        rtc_sync(&projected, instance->time_half_dots);
        rtc_block_write(&projected, out_bytes + instance->cartridge_ram_size);
    }
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
gbb_error gbb_import_battery(gbb_instance *instance, const uint8_t *bytes,
                             size_t size_bytes) {
    if (instance == NULL || bytes == NULL) return GBB_INVALID_ARGUMENT;
    if (!has_battery_image(instance)) return GBB_NO_BATTERY;
    if (size_bytes != battery_image_size(instance)) return GBB_BATTERY_SIZE_MISMATCH;
    const size_t ram_size = instance->cartridge_ram_size;
    /* Parse the clock into a local first so a bad block changes nothing. */
    cart_state parsed = instance->cart;
    if (instance->cart.has_timer) {
        const gbb_error block = rtc_block_parse(bytes + ram_size, &parsed);
        if (block != GBB_OK) return block;
    }
    int changed = 0;
    if (ram_size != 0u) {
        if (instance->cart.kind == CART_MBC2) {
            /* Normalise to the canonical 0xF0 | nibble image and compare first, so
             * an unchanged image is a no-op and the input is never written. */
            for (size_t i = 0u; i < ram_size; ++i)
                if (instance->cartridge_ram[i] != (uint8_t)(0xF0u | (bytes[i] & 0x0Fu)))
                    changed = 1;
            if (changed)
                for (size_t i = 0u; i < ram_size; ++i)
                    instance->cartridge_ram[i] = (uint8_t)(0xF0u | (bytes[i] & 0x0Fu));
        } else if (memcmp(instance->cartridge_ram, bytes, ram_size) != 0) {
            memcpy(instance->cartridge_ram, bytes, ram_size);
            changed = 1;
        }
    }
    if (instance->cart.has_timer) {
        /* Compare against the live clock projected to now, so re-importing an
         * image just exported at this emulated time is not a change. The import
         * itself never advances the clock: the anchor becomes now. */
        cart_state live = instance->cart;
        rtc_sync(&live, instance->time_half_dots);
        if (!rtc_fields_equal(&live, &parsed)) changed = 1;
        instance->cart.rtc_sub = parsed.rtc_sub;
        instance->cart.rtc_s = parsed.rtc_s;
        instance->cart.rtc_m = parsed.rtc_m;
        instance->cart.rtc_h = parsed.rtc_h;
        instance->cart.rtc_dl = parsed.rtc_dl;
        instance->cart.rtc_dh = parsed.rtc_dh;
        memcpy(instance->cart.rtc_l, parsed.rtc_l, 5u);
        instance->cart.rtc_latch_prev = parsed.rtc_latch_prev;
        instance->cart.rtc_synced_at = instance->time_half_dots;
    }
    if (changed && instance->battery_generation != UINT64_MAX)
        ++instance->battery_generation;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
gbb_error gbb_battery_generation(const gbb_instance *instance,
                                 uint64_t *out_generation) {
    if (instance == NULL || out_generation == NULL) return GBB_INVALID_ARGUMENT;
    if (!has_battery_image(instance)) return GBB_NO_BATTERY;
    *out_generation = instance->battery_generation;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
gbb_error gbb_rtc_catch_up(gbb_instance *instance, int64_t elapsed_seconds) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    if (!instance->loaded || !instance->cart.has_timer) return GBB_NO_RTC;
    if (elapsed_seconds < 0) return GBB_INVALID_ARGUMENT;
    if (elapsed_seconds == 0) return GBB_OK;
    cart_state *c = &instance->cart;
    rtc_sync(c, instance->time_half_dots);
    if (c->rtc_dh & 0x40u) return GBB_OK; /* halted: the delta is ignored */
    const cart_state before = *c;
    rtc_add_seconds(c, (uint64_t)elapsed_seconds);
    if (!rtc_fields_equal(&before, c) && c->has_battery &&
        instance->battery_generation != UINT64_MAX)
        ++instance->battery_generation;
    return GBB_OK;
}

/* MODEL: BOTH GATE-00 basis=cartridge-side */
gbb_error gbb_rumble_state(const gbb_instance *instance, uint8_t *out_on,
                           uint64_t *out_changes) {
    if (instance == NULL || out_on == NULL || out_changes == NULL)
        return GBB_INVALID_ARGUMENT;
    if (!instance->loaded || !instance->cart.has_rumble) return GBB_NO_RUMBLE;
    *out_on = instance->cart.rumble_on;
    *out_changes = instance->cart.rumble_changes;
    return GBB_OK;
}

typedef struct { uint8_t size; uint8_t ticks; int supported; } decoded;

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static int is_unused_opcode(uint8_t op) {
    return op == 0xD3 || op == 0xDB || op == 0xDD || op == 0xE3 || op == 0xE4 ||
           op == 0xEB || op == 0xEC || op == 0xED || op == 0xF4 || op == 0xFC || op == 0xFD;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static int condition_true(const gbb_instance *m, unsigned condition) {
    switch (condition & 3u) {
        case 0: return (m->f & 0x80) == 0;
        case 1: return (m->f & 0x80) != 0;
        case 2: return (m->f & 0x10) == 0;
        default: return (m->f & 0x10) != 0;
    }
}

/* MODEL: BOTH GATE-00 basis="CGB speed selection is gated at execution" */
static int stop_case(const gbb_instance *m) {
    /* MODEL: CGB_ONLY GATE-84 GUARD=key1_armed -- armed CGB STOP selects the switch decision table */
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB || !(m->key1_armed & 1u)) /* P12-M8 */
        return 0;
    /* MODEL: UNKNOWN GATE-85 expected-failure:speed-switch-held-button-oracle-only -- armed held-button STOP follows the SameBoy decision */
    const int held = (joypad_value(m) & 0x0Fu) != 0x0Fu; /* P12-M19 */
    /* MODEL: UNKNOWN GATE-86 expected-failure:speed-switch-pending-irq-oracle-only -- pending-IRQ switch and STOP length interpretation is not independently pinned */
    const int pending = (m->ie & m->interrupt_flags & 0x1Fu) != 0; /* P12-M20 */
    return held ? (pending ? 2 : 1) : (pending ? 3 : 4);
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static decoded decode(const gbb_instance *m) {
    uint8_t op = read8(m, m->pc);
    /* MODEL: BOTH GATE-60 basis="no SM83 opcode difference" -- illegal-opcode decode is identical on DMG and CGB */
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
        case 0x00: case 0x07: case 0x0F: case 0x17: case 0x1F:
        case 0x27: case 0x2F: case 0x37: case 0x3F: case 0x76: case 0xC9:
        case 0xD9: case 0xE9: case 0xF3: case 0xFB:
            return (decoded){1, (uint8_t)((op == 0xC9 || op == 0xD9) ? 32 : 8), 1};
        case 0x10: {
            const int selected = stop_case(m);
            return (decoded){(uint8_t)((selected == 2 || selected == 3) ? 1u : 2u),
                (uint8_t)((selected == 3 || selected == 4) /* P12-M29 */
                ? GBB_STOP_SWITCH_COST_HALF_DOTS : 8u), 1};
        }
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

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint8_t instruction_cost(const gbb_instance *m, decoded d) {
    return (uint8_t)(d.ticks >> m->double_speed); /* P12-M18 */ /* instruction-cost */
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint16_t pair_value(const gbb_instance *m, unsigned pair) {
    switch (pair & 3u) {
        case 0: return (uint16_t)(((uint16_t)m->b << 8) | m->c);
        case 1: return (uint16_t)(((uint16_t)m->d << 8) | m->e);
        case 2: return hl(m);
        default: return m->sp;
    }
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static int instruction_reads_supported(gbb_instance *m, decoded d, uint8_t op) {
    /* Address checks have no bus phases or side effects. Every byte is checked
     * before an instruction can change registers, RAM, devices or outputs. */
    for (unsigned i = 0; i < d.size; ++i)
        if (!read_supported(m, instruction_address(m, m->pc, i))) return 0;

    if (op == 0xCB)
        return (instruction_byte(m, m->pc, 1) & 7u) != 6u || read_supported(m, hl(m));
    if ((op >= 0x40 && op <= 0x7F && op != 0x76 && (op & 7u) == 6u) ||
        (op >= 0x80 && op <= 0xBF && (op & 7u) == 6u) ||
        (((op & 0xC7u) == 0x04u || (op & 0xC7u) == 0x05u) && ((op >> 3) & 7u) == 6u) ||
        op == 0x2A || op == 0x3A)
        return read_supported(m, hl(m));

    if ((op & 0xCFu) == 0xC1u || op == 0xC9 || op == 0xD9 ||
        ((op & 0xE7u) == 0xC0u && condition_true(m, (op >> 3) & 3u)))
        return read_supported(m, m->sp) && read_supported(m, (uint16_t)(m->sp + 1u));

    switch (op) {
        case 0x0A: return read_supported(m, pair_value(m, 0));
        case 0x1A: return read_supported(m, pair_value(m, 1));
        case 0xF0: return read_supported(m, (uint16_t)(0xFF00u + instruction_byte(m, m->pc, 1)));
        case 0xF2: return read_supported(m, (uint16_t)(0xFF00u + m->c));
        case 0xFA: {
            uint16_t address = (uint16_t)(instruction_byte(m, m->pc, 1) |
                               ((uint16_t)instruction_byte(m, m->pc, 2) << 8));
            return read_supported(m, address);
        }
        default: return 1; /* Writes to absent ROM-only regions remain ignored. */
    }
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void set_pair(gbb_instance *m, unsigned pair, uint16_t value) {
    switch (pair & 3u) {
        case 0: m->b=(uint8_t)(value>>8); m->c=(uint8_t)value; break;
        case 1: m->d=(uint8_t)(value>>8); m->e=(uint8_t)value; break;
        case 2: set_hl(m,value); break;
        default: m->sp=value; break;
    }
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint16_t stack_pair(const gbb_instance *m, unsigned pair) {
    return pair == 3 ? (uint16_t)(((uint16_t)m->a << 8) | m->f) : pair_value(m,pair);
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void set_stack_pair(gbb_instance *m, unsigned pair, uint16_t value) {
    if (pair == 3) { m->a=(uint8_t)(value>>8); m->f=(uint8_t)(value&0xF0u); }
    else set_pair(m,pair,value);
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint8_t get_reg(gbb_instance *m, unsigned reg, uint64_t offset) {
    switch (reg & 7u) {
        case 0: return m->b; case 1: return m->c; case 2: return m->d; case 3: return m->e;
        case 4: return m->h; case 5: return m->l; case 6: return bus_read(m,hl(m),offset); default: return m->a;
    }
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void set_reg(gbb_instance *m, unsigned reg, uint8_t value, uint64_t offset) {
    switch (reg & 7u) {
        case 0: m->b=value; break; case 1: m->c=value; break; case 2: m->d=value; break; case 3: m->e=value; break;
        case 4: m->h=value; break; case 5: m->l=value; break; case 6: bus_write(m,hl(m),value,offset); break; default: m->a=value; break;
    }
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
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

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint8_t add8(gbb_instance *m, uint8_t lhs, uint8_t rhs, unsigned carry) {
    unsigned sum=(unsigned)lhs+(unsigned)rhs+carry; uint8_t result=(uint8_t)sum;
    m->f=(uint8_t)((result==0?0x80:0)|(((lhs&15u)+(rhs&15u)+carry>15u)?0x20:0)|(sum>255u?0x10:0)); return result;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint8_t sub8(gbb_instance *m, uint8_t lhs, uint8_t rhs, unsigned carry) {
    unsigned sub=(unsigned)rhs+carry; uint8_t result=(uint8_t)((unsigned)lhs-sub);
    m->f=(uint8_t)(0x40|(result==0?0x80:0)|((lhs&15u)<((rhs&15u)+carry)?0x20:0)|((unsigned)lhs<sub?0x10:0)); return result;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
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

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void push16(gbb_instance *m, uint16_t value, uint64_t high_time, uint64_t low_time) {
    --m->sp; bus_write(m,m->sp,(uint8_t)(value>>8),high_time);
    --m->sp; bus_write(m,m->sp,(uint8_t)value,low_time);
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static uint16_t pop16(gbb_instance *m, uint64_t low_time, uint64_t high_time) {
    uint8_t lo=bus_read(m,m->sp,low_time); ++m->sp;
    uint8_t hi=bus_read(m,m->sp,high_time); ++m->sp;
    return (uint16_t)(lo | ((uint16_t)hi<<8));
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void execute(gbb_instance *m, uint8_t cost) {
    uint16_t pc=m->pc; uint8_t op=read8(m,pc); uint64_t base=0;
    if (op>=0x40 && op<=0x7F) {
        /* MODEL: BOTH GATE-61 basis="no SM83 opcode difference" -- HALT and the halt bug */
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
            /* MODEL: UNKNOWN GATE-62 research:14 -- STOP on the DMG, compat and unarmed paths */
            case 0x10:
                /* MODEL: CGB_ONLY GATE-74 GUARD=model_is_cgb -- CGB mode STOP with KEY1 armed takes the implemented speed-switch path (D-01/D-23) */
                if (!model_is_cgb(m)) { m->pc=(uint16_t)(pc+2u); m->stopped=1u; break; }
                switch (stop_case(m)) { /* P12-M33 */
                case 1: m->pc = (uint16_t)(pc + 2u); m->halted = 1u; break;
                case 2: m->pc = (uint16_t)(pc + 1u); break;
                case 3: m->pc = (uint16_t)(pc + 1u); m->stop_switch_pending = 3u; break;
                case 4:
                    m->pc = (uint16_t)(pc + 2u);
                    m->stop_switch_pending = 4u; /* P12-M33 */
                    break;
                default: m->pc=(uint16_t)(pc+2u); m->stopped=1u; break;
                }
                break; /* P12-M34: STOP must not execute RLCA. */
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

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static unsigned pending_interrupt(const gbb_instance *m) {
    uint8_t pending = (uint8_t)(m->ie & m->interrupt_flags & 0x1Fu);
    for (unsigned bit = 0; bit < 5; ++bit) if (pending & (1u << bit)) return bit;
    return 5;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void enter_interrupt(gbb_instance *m, unsigned bit) {
    uint8_t mask = (uint8_t)(1u << bit);
    m->ime = 0;
    m->ime_delay = 0;
    /* Device deadlines at the acknowledge phase precede the IF bus write. */
    advance_devices_to(m, m->instruction_start_half_dots + (8u >> m->double_speed));
    m->interrupt_flags = (uint8_t)(m->interrupt_flags & (uint8_t)~mask);
    observe_bus(m, 0, 0xFF0F, 2, (uint8_t)(0xE0u | m->interrupt_flags));
    /* MODEL: BOTH GATE-63 basis="no SM83 opcode difference" -- interrupt entry timing is a CPU trait */
    push16(m, m->pc, 16, 24);
    m->pc = (uint16_t)(0x0040u + bit * 8u);
    m->halted = 0;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static void save_trace(const gbb_instance *m, decoded d, gbb_trace_record *r) {
    memset(r, 0, sizeof(*r));
    r->time_half_dots = m->time_half_dots; r->pc = m->pc; r->opcode_size = d.size;
    for (uint8_t i = 0; i < d.size && i < 3; ++i) r->opcode[i] = instruction_byte(m, m->pc, i);
    r->a=m->a; r->f=m->f; r->b=m->b; r->c=m->c; r->d=m->d; r->e=m->e; r->h=m->h; r->l=m->l; r->sp=m->sp;
}

/* Private regression seam, like the bus observer: no guest execution or reads. */
/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
void gbb_test_cpu_snapshot(const gbb_instance *m, gbb_trace_record *record) {
    if (m != NULL && record != NULL) save_trace(m, (decoded){0, 0, 1}, record);
}

/* Private test seam: the address of the last refused read pre-flight or deferred/serial write.
 * Not public ABI; read only by tests. */
/* MODEL: BOTH GATE-00 basis="debug seam" */
uint16_t gbb_test_last_unsupported_address(const gbb_instance *m) {
    return m == NULL ? 0u : m->bus_unsupported_address;
}

/* Private test seam, like gbb_test_cpu_snapshot: reports the effective banks, never public ABI. */
/* MODEL: BOTH GATE-00 basis="DMG pins wram_bank=1 and vram_bank=0" */
void gbb_test_bank_state(const gbb_instance *m, uint8_t *out_vram_bank, uint8_t *out_wram_bank) {
    if (m == NULL) return;
    if (out_vram_bank != NULL) *out_vram_bank = m->vram_bank;
    if (out_wram_bank != NULL) *out_wram_bank = m->wram_bank;
}

/* Private test seam for Phase 12 speed-switch state; NULL outputs are ignored. */
/* MODEL: BOTH GATE-00 basis="test seam reports private per-instance state" */
void gbb_test_speed_state(const gbb_instance *m, uint8_t *double_speed,
                          uint8_t *stall_kind, uint32_t *stall_half_dots,
                          uint8_t *key1_armed) {
    if (m == NULL) return;
    if (double_speed != NULL) *double_speed = m->double_speed;
    if (stall_kind != NULL) *stall_kind = m->cpu_stall_kind;
    if (stall_half_dots != NULL) *stall_half_dots = m->cpu_stall_half_dots;
    if (key1_armed != NULL) *key1_armed = m->key1_armed;
}

/* Private test seam: reports the exact per-instance master clock without advancing it. */
/* MODEL: BOTH GATE-00 basis="test seam reads the instance clock" */
uint64_t gbb_test_master_time_half_dots(const gbb_instance *m) {
    return m == NULL ? 0u : m->time_half_dots;
}

/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */
static int halt_bug_keeps_control_target(const gbb_instance *m, uint8_t op) {
    if (op == 0xC3 || op == 0xC9 || op == 0xCD || op == 0xD9 || op == 0xE9 || (op & 0xC7u) == 0xC7u) return 1;
    if ((op & 0xE7u) == 0xC0u || (op & 0xE7u) == 0xC2u || (op & 0xE7u) == 0xC4u)
        return condition_true(m, (op >> 3) & 3u);
    return 0;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int cpu_stalled(const gbb_instance *m) {
    return m->cpu_stall_kind != GBB_STALL_NONE;
}

/* MODEL: CGB_ONLY GATE-99 GUARD=model_is_cgb -- an accepted FF55 start reserves checked master-time headroom for its finite byte work */
static int hdma_start_headroom_available(const gbb_instance *m, uint8_t value,
                                         uint64_t operation_cost) {
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB ||
        m->hdma.mode == 2u || m->hdma.active ||
        (m->hdma.mode == 1u && (value & 0x80u) == 0u)) return 1;
    const uint64_t blocks = (uint64_t)(value & 0x7Fu) + 1u;
    if (blocks > (UINT64_MAX - operation_cost) / UINT64_C(64)) return 0;
    const uint64_t required = operation_cost + blocks * UINT64_C(64);
    return UINT64_MAX - m->time_half_dots >= required;
}

/* MODEL: BOTH GATE-00 basis="model-neutral function; see its branch gates" */
static int hdma_stack_push_headroom_available(const gbb_instance *m,
                                              uint16_t value,
                                              uint64_t operation_cost) {
    const uint16_t high_address = (uint16_t)(m->sp - 1u);
    const uint16_t low_address = (uint16_t)(m->sp - 2u);
    if (high_address == 0xFF55u &&
        !hdma_start_headroom_available(m, (uint8_t)(value >> 8), operation_cost)) return 0;
    if (low_address == 0xFF55u &&
        !hdma_start_headroom_available(m, (uint8_t)value, operation_cost)) return 0;
    return 1;
}

/* Resolve CPU stores to FF55 before their bus phases, so a rejected start
 * cannot partially change CPU state, another register, or output buffers. */
/* MODEL: BOTH GATE-00 basis="model-neutral function; see its branch gates" */
static int hdma_instruction_headroom_available(const gbb_instance *m,
                                               uint8_t opcode,
                                               uint64_t operation_cost) {
    uint16_t address = 0u;
    uint8_t value = 0u;
    int writes = 0;
    if (opcode == 0xE0u) {
        address = (uint16_t)(0xFF00u + instruction_byte(m, m->pc, 1u));
        value = m->a;
        writes = 1;
    } else if (opcode == 0xE2u) {
        address = (uint16_t)(0xFF00u + m->c);
        value = m->a;
        writes = 1;
    } else if (opcode == 0xEAu) {
        address = (uint16_t)(instruction_byte(m, m->pc, 1u) |
            ((uint16_t)instruction_byte(m, m->pc, 2u) << 8));
        value = m->a;
        writes = 1;
    } else if (opcode == 0x02u || opcode == 0x12u ||
               opcode == 0x22u || opcode == 0x32u) {
        address = opcode == 0x02u ? pair_value(m, 0u) :
                  opcode == 0x12u ? pair_value(m, 1u) : hl(m);
        value = m->a;
        writes = 1;
    } else if (opcode >= 0x70u && opcode <= 0x77u && opcode != 0x76u) {
        address = hl(m);
        value = get_reg((gbb_instance *)m, opcode & 7u, 0u);
        writes = 1;
    } else if (opcode == 0x36u && hl(m) == 0xFF55u) {
        address = hl(m);
        value = instruction_byte(m, m->pc, 1u);
        writes = 1;
    } else if (((opcode & 0xC7u) == 0x04u || (opcode & 0xC7u) == 0x05u) &&
               ((opcode >> 3) & 7u) == 6u && hl(m) == 0xFF55u) {
        address = hl(m);
        const uint8_t old = read8(m, address);
        value = (opcode & 1u) != 0u ? (uint8_t)(old - 1u) : (uint8_t)(old + 1u);
        writes = 1;
    } else if (opcode == 0xCBu) {
        const uint8_t extension = instruction_byte(m, m->pc, 1u);
        const unsigned group = extension >> 6;
        const unsigned operation = (extension >> 3) & 7u;
        if ((extension & 7u) == 6u && group != 1u && hl(m) == 0xFF55u) {
            address = hl(m);
            value = read8(m, address);
            if (group == 0u) {
                const uint8_t carry_in = (uint8_t)((m->f & 0x10u) != 0u);
                switch (operation) {
                case 0u: value = (uint8_t)((value << 1) | (value >> 7)); break;
                case 1u: value = (uint8_t)((value >> 1) | (value << 7)); break;
                case 2u: value = (uint8_t)((value << 1) | carry_in); break;
                case 3u: value = (uint8_t)((value >> 1) | (carry_in << 7)); break;
                case 4u: value = (uint8_t)(value << 1); break;
                case 5u: value = (uint8_t)((value >> 1) | (value & 0x80u)); break;
                case 6u: value = (uint8_t)((value << 4) | (value >> 4)); break;
                default: value = (uint8_t)(value >> 1); break;
                }
            } else if (group == 2u) {
                value = (uint8_t)(value & (uint8_t)~(1u << operation));
            } else {
                value = (uint8_t)(value | (uint8_t)(1u << operation));
            }
            writes = 1;
        }
    } else if (opcode == 0x08u) {
        address = (uint16_t)(instruction_byte(m, m->pc, 1u) |
            ((uint16_t)instruction_byte(m, m->pc, 2u) << 8));
        if (address == 0xFF55u)
            return hdma_start_headroom_available(m, (uint8_t)m->sp, operation_cost);
        if ((uint16_t)(address + 1u) == 0xFF55u)
            return hdma_start_headroom_available(m, (uint8_t)(m->sp >> 8), operation_cost);
    } else if ((opcode & 0xCFu) == 0xC5u) {
        return hdma_stack_push_headroom_available(m,
            stack_pair(m, (opcode >> 4) & 3u), operation_cost);
    } else if (opcode == 0xCDu ||
               ((opcode & 0xE7u) == 0xC4u && condition_true(m, (opcode >> 3) & 3u))) {
        const uint16_t pushed = (uint16_t)(m->pc + 3u - (m->halt_bug ? 1u : 0u));
        return hdma_stack_push_headroom_available(m, pushed, operation_cost);
    } else if ((opcode & 0xC7u) == 0xC7u) {
        const uint16_t pushed = (uint16_t)(m->pc + (m->halt_bug ? 0u : 1u));
        return hdma_stack_push_headroom_available(m, pushed, operation_cost);
    }
    if (!writes || address != 0xFF55u) return 1;
    return hdma_start_headroom_available(m, value, operation_cost);
}

/* MODEL: BOTH GATE-00 basis="normal-speed phase alignment is guarded and a no-op outside CGB mode" */
static void speed_switch_apply_realign(gbb_instance *m) {
    /* MODEL: UNKNOWN GATE-89 expected-failure:speed-switch-odd-mode-alignment -- entry into normal speed may land in an unsupported odd PPU mode phase */
    if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB ||
        m->double_speed != 0u || (m->time_half_dots & 7u) != 4u) return; /* P12-M23 */
    m->cpu_stall_kind = GBB_STALL_SWITCH_REALIGN;
    m->cpu_stall_half_dots = 4u;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static gbb_run_result gbb_run_internal(gbb_instance *instance, uint64_t budget_half_dots,
                                       gbb_trace_record *trace, size_t trace_capacity) {
    gbb_run_result result={0, GBB_STOP_BUDGET, 0, 0, 0, 0};
    if (instance == NULL || !instance->loaded || (trace == NULL && trace_capacity != 0)) { result.reason=GBB_STOP_INVALID_STATE; return result; }
    if (GBB_P13_MUT(53) && instance->hdma.active)
        instance->hdma.byte_phase = 0u; /* P13-05-M14: run boundary drops byte remainder */
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
        /* MODEL: CGB_ONLY GATE-87 GUARD=cpu_stalled -- CGB switch pause uses its bounded run-loop stall branch */
        if (cpu_stalled(instance)) {
            /* MODEL: UNKNOWN GATE-88 expected-failure:speed-switch-wake-oracle-only -- only the IME-on wake has an AGE hardware row */
            const int wake_pending =
                (instance->ie & instance->interrupt_flags & 0x1Fu) != 0; /* P12-M16 */
            const uint32_t quantum = 8u >> instance->double_speed;
            const uint32_t stall_phase = instance->cpu_stall_half_dots % quantum;
            if (instance->cpu_stall_kind == GBB_STALL_SPEED_SWITCH && wake_pending) { /* P12-M13 */
                if (GBB_P13_MUT(50)) { /* P13-05-M11: IRQ wake loses admitted DMA */
                    instance->hdma.active = 0u;
                    instance->hdma.pending_hblank = 0u;
                    instance->hdma.blocks_remaining = 0u;
                }
                if (stall_phase == 0u) {
                    instance->cpu_stall_kind = GBB_STALL_NONE;
                    instance->cpu_stall_half_dots = 0u;
                    speed_switch_apply_realign(instance);
                    continue;
                }
            }
            const int hdma_active = instance->hdma.active != 0u;
            const int hdma_pending_at_boundary =
                instance->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
                instance->hdma.pending_hblank && stall_phase == 0u;
            const uint32_t to_boundary = stall_phase == 0u ? quantum : stall_phase;
            const uint32_t desired_step = (hdma_active ||
                (instance->cpu_stall_kind == GBB_STALL_SPEED_SWITCH &&
                 instance->hdma.pending_hblank)) ? 1u : to_boundary;
            const uint32_t step = instance->cpu_stall_half_dots < desired_step
                ? instance->cpu_stall_half_dots : desired_step;
            if (step == 0u) {
                instance->cpu_stall_kind = GBB_STALL_NONE;
                continue;
            }
            if (budget_half_dots - result.consumed_half_dots < step) return result; /* P12-M9 */
            if (!audio_preflight(instance, step)) {
                result.reason = GBB_STOP_OUTPUT_FULL;
                return result;
            }
            if (UINT64_MAX - instance->time_half_dots < step) {
                result.reason = GBB_STOP_INVALID_STATE;
                return result;
            }
            if (instance->diagnostic_output != NULL &&
                instance->diagnostic_output_capacity - instance->diagnostic_output_count <
                    GBB_DIAGNOSTIC_OPERATION_RESERVE) {
                result.reason = GBB_STOP_OUTPUT_FULL;
                return result;
            }
            if (hdma_pending_at_boundary && !hdma_admit_block(instance)) {
                hdma_stop_at_invalid_block(instance, instance->hdma.source_cursor);
                instance->bus_unsupported = 0;
                result.reason = GBB_STOP_UNSUPPORTED_BUS;
                return result;
            }
            gbb_diagnostic_record operation[GBB_DIAGNOSTIC_OPERATION_RESERVE];
            if (instance->diagnostic_output != NULL) {
                instance->diagnostic_operation = operation;
                instance->diagnostic_operation_count = 0u;
            }
            advance_devices(instance, step); /* P12-M7 */
            if (instance->diagnostic_output != NULL) diagnostic_commit(instance);
            instance->cpu_stall_half_dots -= step;
            result.consumed_half_dots += step;
            if (instance->cpu_stall_half_dots == 0u) {
                instance->cpu_stall_kind = GBB_STALL_NONE;
                speed_switch_apply_realign(instance);
            }
            continue;
        }
        /* Service a latched HBlank request before interrupt dispatch or a new
         * opcode. The current instruction has already retired, so its final
         * bus access and event trace remain whole. Each committed master tick
         * is independently bounded by the caller's outputs and budget. */
        if (instance->hdma.pending_hblank ||
            (instance->hdma.active && !GBB_P13_MUT(40))) { /* P13-05-M01: no-steal discriminator */
            if (budget_half_dots - result.consumed_half_dots < 1u) return result;
            if (!audio_preflight(instance, 1u)) {
                result.reason = GBB_STOP_OUTPUT_FULL;
                return result;
            }
            if (UINT64_MAX - instance->time_half_dots < 1u) {
                result.reason = GBB_STOP_INVALID_STATE;
                return result;
            }
            if (instance->diagnostic_output != NULL &&
                instance->diagnostic_output_capacity - instance->diagnostic_output_count <
                    GBB_DIAGNOSTIC_OPERATION_RESERVE) {
                result.reason = GBB_STOP_OUTPUT_FULL;
                return result;
            }
            if (instance->hdma.pending_hblank && !hdma_admit_block(instance)) {
                hdma_stop_at_invalid_block(instance, instance->hdma.source_cursor);
                instance->bus_unsupported = 0;
                result.reason = GBB_STOP_UNSUPPORTED_BUS;
                return result;
            }
            gbb_diagnostic_record operation[GBB_DIAGNOSTIC_OPERATION_RESERVE];
            if (instance->diagnostic_output != NULL) {
                instance->diagnostic_operation = operation;
                instance->diagnostic_operation_count = 0u;
            }
            advance_devices(instance, 1u);
            if (instance->diagnostic_output != NULL) diagnostic_commit(instance);
            ++result.consumed_half_dots;
            if (instance->bus_unsupported) {
                instance->bus_unsupported = 0;
                result.reason = GBB_STOP_UNSUPPORTED_BUS;
                return result;
            }
            continue;
        }
        unsigned interrupt = instance->ime ? pending_interrupt(instance) : 5;
        if (interrupt < 5) {
            const uint32_t irq_cost = 40u >> instance->double_speed;
            if (irq_cost > budget_half_dots - result.consumed_half_dots) return result;
            if (!audio_preflight(instance, irq_cost)) { result.reason=GBB_STOP_OUTPUT_FULL; return result; }
            if (!hdma_stack_push_headroom_available(instance, instance->pc, irq_cost)) {
                result.reason = GBB_STOP_INVALID_STATE;
                return result;
            }
            if (UINT64_MAX - instance->time_half_dots < irq_cost) { result.reason=GBB_STOP_INVALID_STATE; return result; }
            gbb_diagnostic_record operation[GBB_DIAGNOSTIC_OPERATION_RESERVE];
            if (instance->diagnostic_output != NULL &&
                instance->diagnostic_output_capacity - instance->diagnostic_output_count < GBB_DIAGNOSTIC_OPERATION_RESERVE) {
                result.reason=GBB_STOP_OUTPUT_FULL; return result;
            }
            diagnostic_begin(instance, operation, instance->pc, 0);
            instance->instruction_start_half_dots = instance->time_half_dots;
            enter_interrupt(instance, interrupt);
            advance_devices_to(instance, instance->instruction_start_half_dots + irq_cost);
            diagnostic_commit(instance);
            result.consumed_half_dots += irq_cost;
            /* The entry push can itself hit a deferred register; report it at this boundary. */
            if (instance->bus_unsupported) {
                instance->bus_unsupported = 0;
                result.reason = GBB_STOP_UNSUPPORTED_BUS;
                return result;
            }
            continue;
        }
        if (instance->halted) {
            if ((instance->ie & instance->interrupt_flags & 0x1Fu) != 0) {
                instance->halted=0;
                result.reason=GBB_STOP_BUDGET;
                continue;
            }
            const uint32_t m_cycle = 8u >> instance->double_speed;
            if (budget_half_dots - result.consumed_half_dots < m_cycle) return result;
            if (!audio_preflight(instance, m_cycle)) { result.reason=GBB_STOP_OUTPUT_FULL; return result; }
            if (UINT64_MAX - instance->time_half_dots < m_cycle) { result.reason=GBB_STOP_INVALID_STATE; return result; }
            /* HALT samples wake conditions at each machine-cycle boundary.
             * A timer/serial interrupt midway through a long budget must wake
             * at the same boundary as it does through shorter run calls. */
            advance_devices(instance, m_cycle);
            result.consumed_half_dots += m_cycle;
            result.reason=GBB_STOP_HALTED_IDLE;
            if ((instance->ie & instance->interrupt_flags & 0x1Fu) != 0) {
                instance->halted=0;
                result.reason=GBB_STOP_BUDGET;
            }
            continue;
        }
        if (!read_supported(instance, instance->pc)) { result.reason=GBB_STOP_UNSUPPORTED_BUS; return result; }
        uint8_t opcode = read8(instance, instance->pc);
        /* CB decoding consumes its extension byte, so check it before decode. */
        if (opcode == 0xCB && !read_supported(instance, instruction_address(instance, instance->pc, 1))) {
            result.reason=GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
        /* MODEL: BOTH GATE-64 basis="no SM83 opcode difference" -- illegal-opcode lockup is a CPU trait */
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
        if (!audio_preflight(instance, cost)) { result.reason=GBB_STOP_OUTPUT_FULL; return result; }
        if (!hdma_instruction_headroom_available(instance, opcode, cost)) {
            result.reason = GBB_STOP_INVALID_STATE;
            return result;
        }
        if (opcode == 0x10u) {
            const int selected_stop_case = stop_case(instance);
            if (selected_stop_case == 3 || selected_stop_case == 4) {
                const uint64_t switch_headroom = (uint64_t)cost +
                    2u * (uint64_t)GBB_SPEED_SWITCH_STALL_T + 4u;
                if (UINT64_MAX - instance->time_half_dots < switch_headroom) { /* P12-M22 */
                    result.reason = GBB_STOP_INVALID_STATE;
                    return result;
                }
            }
        }
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
        if (instance->ime_delay != 0 && --instance->ime_delay == 0) instance->ime = 1; /* P12-M34 */
        if (instance->stop_switch_pending == 3u || instance->stop_switch_pending == 4u) {
            const uint8_t switch_case = instance->stop_switch_pending;
            instance->stop_switch_pending = 0u;
            divider_reset(instance, 1); /* P12-M27 */
            instance->double_speed ^= 1u; /* P12-M11 */
            instance->key1_armed = 0u; /* P12-M10 */
            if (switch_case == 4u) {
                instance->cpu_stall_kind = GBB_STALL_SPEED_SWITCH; /* P12-M5 */
                instance->cpu_stall_half_dots = GBB_SPEED_SWITCH_STALL_T *
                    (instance->double_speed ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL); /* P12-M6 */
            } else {
                speed_switch_apply_realign(instance);
            }
            continue;
        }
        /* MODEL: BOTH GATE-65 basis="DIV and the divider phase reset at STOP on both models; shared divider_reset, D-02/D-39" */
        if (instance->stopped) {
            divider_reset(instance, 0); /* P12-M30 */
            result.reason=GBB_STOP_STOPPED;
            return result;
        }
        if (instance->bus_unsupported) {
            instance->bus_unsupported = 0;
            result.reason = GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
        if (instance->halted) { result.reason=GBB_STOP_HALTED_IDLE; return result; }
    }
    return result;
}

/* MODEL: BOTH GATE-00 basis=host-api */
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

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity) {
    return gbb_run_ex(instance, budget_half_dots, trace, trace_capacity, NULL, 0);
}

/* MODEL: BOTH GATE-00 basis=host-api */
gbb_run_result gbb_run_audio(gbb_instance *instance, uint64_t budget_half_dots,
                             gbb_audio_frame *frames, size_t frame_capacity,
                             size_t *out_frame_count) {
    gbb_run_result invalid = {0, GBB_STOP_INVALID_STATE, 0, 0, 0, 0};
    if (out_frame_count == NULL) return invalid;
    *out_frame_count = 0u;
    if ((frames == NULL && frame_capacity != 0u) || instance == NULL ||
        instance->audio_run_active || instance->diagnostic_output != NULL)
        return invalid;
    if (frames != NULL && frame_capacity != 0u) {
        if (frame_capacity > SIZE_MAX / sizeof(*frames)) return invalid;
        const uintptr_t frame_begin = (uintptr_t)(void *)frames;
        const uintptr_t count_begin = (uintptr_t)(void *)out_frame_count;
        const size_t frame_bytes = frame_capacity * sizeof(*frames);
        if (frame_bytes > UINTPTR_MAX - frame_begin ||
            sizeof(*out_frame_count) > UINTPTR_MAX - count_begin)
            return invalid;
        const uintptr_t frame_end = frame_begin + frame_bytes;
        const uintptr_t count_end = count_begin + sizeof(*out_frame_count);
        if (frame_begin < count_end && count_begin < frame_end) return invalid;
    }
    instance->audio_frames = frames;
    instance->audio_frame_capacity = frame_capacity;
    instance->audio_frame_count = 0u;
    instance->audio_run_active = 1;
    gbb_run_result result = gbb_run_internal(instance, budget_half_dots, NULL, 0u);
    *out_frame_count = instance->audio_frame_count;
    instance->audio_frames = NULL;
    instance->audio_frame_capacity = 0u;
    instance->audio_frame_count = 0u;
    instance->audio_run_active = 0;
    return result;
}

/* MODEL: BOTH GATE-00 basis=see-branch-gates */
uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address) {
    if (instance == NULL) return 0xFF;
    /* MODEL: BOTH GATE-66 basis=wram-echo-map -- debug peek of work RAM */
    if (address >= 0xC000 && address <= 0xFDFF) return *wram_byte(instance, address);
    if (address >= 0xFF80 && address <= 0xFFFE) return instance->hram[address - 0xFF80];
    return 0xFF;
}
